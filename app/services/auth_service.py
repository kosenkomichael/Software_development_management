import hashlib
import json
import secrets
import uuid

from fastapi import BackgroundTasks, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.security import credential_version, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, ProfileUpdateRequest, RegisterRequest, TokenResponse
from app.services.mail_service import send_password_reset

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

        user = await self._repo.get_by_id(uuid.UUID(user_id))
        if (
            user is None
            or not user.is_active
            or payload.get("cv") != credential_version(user.hashed_password)
        ):
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        stored = await self._redis.getdel(f"refresh:{jti}")
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired",
            )

        # rotate: invalidate old token, issue new pair
        return await self._issue_tokens(user_id)

    async def logout(self, refresh_token: str) -> None:
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            return  # already invalid — nothing to revoke
        jti: str = payload["jti"]
        await self._redis.delete(f"refresh:{jti}")

    async def _issue_tokens(self, user_id: str) -> TokenResponse:
        user = await self._repo.get_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        version = credential_version(user.hashed_password)
        access = create_access_token(user_id, version)
        refresh, jti = create_refresh_token(user_id, version)
        await self._redis.setex(f"refresh:{jti}", _REFRESH_TTL, user_id)
        return TokenResponse(access_token=access, refresh_token=refresh)

    async def forgot_password(self, email: str, background: BackgroundTasks) -> int:
        user = await self._repo.get_by_email(email)
        if user is None or not user.is_active:
            raise HTTPException(status_code=404, detail="Recovery account not found")
        email_key = hashlib.sha256(email.encode()).hexdigest()
        cooldown_key = f"reset-cooldown:{email_key}"
        if not await self._redis.set(cooldown_key, "1", ex=60, nx=True):
            return max(1, await self._redis.ttl(cooldown_key))
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        await self._redis.setex(
            f"password-reset:{digest}",
            1800,
            json.dumps({"uid": str(user.id), "cv": credential_version(user.hashed_password)}),
        )
        link = f"{settings.frontend_url.rstrip('/')}/reset-password#token={token}"
        background.add_task(send_password_reset, user.email, link)
        return 60

    async def reset_password(self, token: str, password: str) -> None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        stored = await self._redis.getdel(f"password-reset:{digest}")
        invalid = HTTPException(status_code=400, detail="Invalid or expired reset link")
        if stored is None:
            raise invalid
        data = json.loads(stored)
        result = await self._session.execute(
            select(User).where(User.id == uuid.UUID(data["uid"])).with_for_update()
        )
        user = result.scalar_one_or_none()
        if (
            user is None
            or not user.is_active
            or data["cv"] != credential_version(user.hashed_password)
        ):
            raise invalid
        user.hashed_password = hash_password(password)
        await self._session.commit()

    async def update_profile(
        self, user_id: uuid.UUID, data: ProfileUpdateRequest
    ) -> tuple[User, TokenResponse | None]:
        user = await self._session.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        email_changed = data.email is not None and data.email != user.email
        if email_changed and data.email is not None:
            if not data.current_password or not verify_password(
                data.current_password, user.hashed_password
            ):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            user.email = data.email
            # Rehash to revoke old sessions and password-reset links after email changes.
            user.hashed_password = hash_password(data.current_password)
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.last_name is not None:
            user.last_name = data.last_name
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise HTTPException(status_code=409, detail="Email already registered") from None
        tokens = await self._issue_tokens(str(user.id)) if email_changed else None
        return user, tokens

    async def change_password(
        self, user_id: uuid.UUID, current_password: str, password: str
    ) -> TokenResponse:
        user = await self._session.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="New password must differ")
        user.hashed_password = hash_password(password)
        await self._session.commit()
        return await self._issue_tokens(str(user.id))
