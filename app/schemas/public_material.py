import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MaterialPublicationRequest(BaseModel):
    is_public: bool
    visibility: Literal["public", "link", "groups"] | None = None
    group_ids: list[uuid.UUID] | None = Field(default=None, max_length=100)
    rotate_link: bool = False
    title: str | None = Field(default=None, min_length=1, max_length=200)


class MaterialPublicationResponse(BaseModel):
    is_public: bool
    title: str
    has_quiz: bool
    visibility: Literal["public", "link", "groups"] = "public"
    group_ids: list[str] = Field(default_factory=list)
    share_token: str | None = None


class PublicMaterialSummary(BaseModel):
    visibility: Literal["public", "link", "groups"] = "public"
    id: str
    title: str
    author: str
    published_at: datetime
    size_bytes: int
    has_quiz: bool


class PublicMaterialDetail(PublicMaterialSummary):
    filename: str
    content_type: str
    note_content: str
    quiz_id: str | None


class PublicMaterialList(BaseModel):
    items: list[PublicMaterialSummary]
    total: int


class MaterialImportResponse(BaseModel):
    material_id: str
    imported: bool


class SharingGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    emails: list[str] = Field(default_factory=list, max_length=200)

    @field_validator("emails")
    @classmethod
    def valid_emails(cls, values: list[str]) -> list[str]:
        result = []
        for value in values:
            value = value.strip().lower()
            if len(value) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
                raise ValueError("Invalid email format")
            result.append(value)
        return sorted(set(result))


class SharingGroupResponse(BaseModel):
    id: str
    name: str
    emails: list[str]
