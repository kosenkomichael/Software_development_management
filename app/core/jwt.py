import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = (
        {"jti": str(uuid.uuid4())}
        | data
        | {
            "exp": datetime.now(UTC) + expires_delta,
            "iat": datetime.now(UTC),
        }
    )
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: str, version: str = "") -> str:
    return _create_token(
        {"sub": user_id, "type": "access", "cv": version},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str, version: str = "") -> tuple[str, str]:
    jti = str(uuid.uuid4())
    token = _create_token(
        {"sub": user_id, "type": "refresh", "jti": jti, "cv": version},
        timedelta(days=settings.refresh_token_expire_days),
    )
    return token, jti


def create_download_token(user_id: str, material_id: str) -> str:
    return _create_token(
        {"sub": user_id, "mid": material_id, "type": "download"},
        timedelta(hours=24),
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def decode_download_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "download":
            return None
        return payload
    except JWTError:
        return None
