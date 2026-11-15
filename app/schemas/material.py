from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.material import MaterialStatus


class MaterialResponse(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: MaterialStatus
    created_at: datetime
    source_author: str | None = None
    is_favorite: bool = False
    download_url: str | None = None


class MaterialListResponse(BaseModel):
    items: list[MaterialResponse]
    total: int


class MaterialUpdateRequest(BaseModel):
    original_filename: str | None = Field(default=None, min_length=1, max_length=255)
    is_favorite: bool | None = None

    @field_validator("original_filename")
    @classmethod
    def validate_filename(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or any(ord(c) < 32 or c in "/\\" for c in value):
            raise ValueError("Invalid material name")
        return value
