from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

_REFRESH_TTL = 60 * 60 * 24 * 7  # 7 days in seconds


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._repo = UserRepository(session)
        self._session = session
        self._redis = redis

    async def register(self, data: RegisterRequest) -> User:
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = User(email=data.email, hashed_password=hash_password(data.password))
        await self._repo.save(user)
        await self._session.commit()
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        return await self._issue_tokens(str(user.id))

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        jti: str = payload["jti"]
        user_id: str = payload["sub"]

        stored = await self._redis.get(f"refresh:{jti}")
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired",
            )

        # rotate: invalidate old token, issue new pair
        await self._redis.delete(f"refresh:{jti}")
        return await self._issue_tokens(user_id)

    async def logout(self, refresh_token: str) -> None:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            return  # already invalid — nothing to revoke
        jti: str = payload["jti"]
        await self._redis.delete(f"refresh:{jti}")

    async def _issue_tokens(self, user_id: str) -> TokenResponse:
        access = create_access_token(user_id)
        refresh, jti = create_refresh_token(user_id)
        await self._redis.setex(f"refresh:{jti}", _REFRESH_TTL, user_id)
        return TokenResponse(access_token=access, refresh_token=refresh)
