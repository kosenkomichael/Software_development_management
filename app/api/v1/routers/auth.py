from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import Float, and_, cast, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.redis import Redis, get_redis
from app.db.session import get_session
from app.models.material import Material
from app.models.quiz_attempt import QuizAttempt
from app.schemas.auth import (
    AccountStatsResponse,
    ActivityItem,
    ActivityResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
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
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
    )


@router.post("/forgot-password", status_code=202)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    background: BackgroundTasks,
    svc: Annotated[AuthService, Depends(_service)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, str | int]:
    host = request.client.host if request.client else "unknown"
    key = f"password-reset-limit:{host}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 600)
    if count > 10:
        raise HTTPException(status_code=429, detail="Too many requests")
    retry_after = await svc.forgot_password(data.email, background)
    return {"message": "Password reset requested", "retry_after": retry_after}


@router.post("/reset-password", status_code=204)
async def reset_password(
    data: ResetPasswordRequest,
    svc: Annotated[AuthService, Depends(_service)],
) -> None:
    await svc.reset_password(data.token, data.password)


@router.patch("/me", response_model=ProfileUpdateResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: CurrentUser,
    svc: Annotated[AuthService, Depends(_service)],
) -> ProfileUpdateResponse:
    user, tokens = await svc.update_profile(current_user.id, data)
    return ProfileUpdateResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            first_name=user.first_name,
            last_name=user.last_name,
        ),
        tokens=tokens,
    )


@router.post("/change-password", response_model=TokenResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    svc: Annotated[AuthService, Depends(_service)],
) -> TokenResponse:
    return await svc.change_password(current_user.id, data.current_password, data.password)


@router.get("/me/stats", response_model=AccountStatsResponse)
async def account_stats(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountStatsResponse:
    materials_count = await session.scalar(
        select(func.count())
        .select_from(Material)
        .where(
            Material.user_id == current_user.id,
            Material.deleted_at.is_(None),
        )
    )
    row = (
        await session.execute(
            select(func.count(QuizAttempt.id), func.avg(QuizAttempt.score))
            .outerjoin(Material, Material.id == QuizAttempt.material_id)
            .where(
                QuizAttempt.user_id == current_user.id,
                or_(
                    QuizAttempt.is_public_attempt.is_(True),
                    and_(Material.user_id == current_user.id, Material.deleted_at.is_(None)),
                ),
            )
        )
    ).one()
    return AccountStatsResponse(
        materials_count=materials_count or 0,
        attempts_count=row[0],
        average_score=float(row[1]) if row[1] is not None else None,
    )


@router.get("/me/activity", response_model=ActivityResponse)
async def account_activity(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
) -> ActivityResponse:
    visible = (Material.user_id == current_user.id, Material.deleted_at.is_(None))
    uploads = select(
        Material.id.label("id"),
        literal("upload").label("kind"),
        Material.id.label("material_id"),
        Material.original_filename.label("title"),
        Material.created_at.label("created_at"),
        cast(literal(None), Float).label("score"),
        literal(False).label("is_public"),
    ).where(*visible)
    attempts = (
        select(
            QuizAttempt.id,
            literal("attempt"),
            QuizAttempt.material_id,
            func.coalesce(
                QuizAttempt.quiz_snapshot["title"].astext, Material.original_filename, "Тест"
            ),
            QuizAttempt.created_at,
            QuizAttempt.score,
            QuizAttempt.is_public_attempt,
        )
        .outerjoin(Material, Material.id == QuizAttempt.material_id)
        .where(
            or_(QuizAttempt.is_public_attempt.is_(True), and_(*visible)),
            QuizAttempt.user_id == current_user.id,
        )
    )
    events = union_all(uploads, attempts).subquery()
    total = await session.scalar(select(func.count()).select_from(events))
    rows = await session.execute(
        select(events)
        .order_by(
            events.c.created_at.desc(),
            events.c.id.desc(),
        )
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return ActivityResponse(
        items=[
            ActivityItem(
                id=str(row.id),
                kind=row.kind,
                material_id=str(row.material_id) if row.material_id else "",
                is_public=row.is_public,
                title=row.title,
                created_at=row.created_at,
                score=row.score,
            )
            for row in rows
        ],
        total=total or 0,
    )
