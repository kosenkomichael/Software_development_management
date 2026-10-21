from datetime import datetime

from pydantic import BaseModel

from app.models.material import MaterialStatus


class MaterialResponse(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: MaterialStatus
    created_at: datetime
    download_url: str | None = None


class MaterialListResponse(BaseModel):
    items: list[MaterialResponse]
    total: int
