from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.redis import Redis, get_redis
from app.db.session import get_session
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthService:
    return AuthService(session, redis)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: RegisterRequest,
    svc: Annotated[AuthService, Depends(_service)],
) -> UserResponse:
    user = await svc.register(data)
    return UserResponse(id=str(user.id), email=user.email, is_active=user.is_active)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    svc: Annotated[AuthService, Depends(_service)],
) -> TokenResponse:
    return await svc.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    svc: Annotated[AuthService, Depends(_service)],
) -> TokenResponse:
    return await svc.refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    data: RefreshRequest,
    svc: Annotated[AuthService, Depends(_service)],
) -> None:
    await svc.logout(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
    )
