from datetime import datetime

from pydantic import BaseModel, Field


class MaterialPublicationRequest(BaseModel):
    is_public: bool
    title: str | None = Field(default=None, min_length=1, max_length=200)


class MaterialPublicationResponse(BaseModel):
    is_public: bool
    title: str
    has_quiz: bool


class PublicMaterialSummary(BaseModel):
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
