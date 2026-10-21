from datetime import datetime

from pydantic import BaseModel

from app.models.material import MaterialStatus


class NoteResponse(BaseModel):
    id: str
    material_id: str
    content: str
    llm_model: str
    generation_time_ms: int
    created_at: datetime


class NoteStatusResponse(BaseModel):
    material_id: str
    status: MaterialStatus
    note_id: str | None = None
