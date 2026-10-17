from uuid import UUID

from sqlalchemy import select

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    model = Note

    async def get_by_material(self, material_id: UUID) -> Note | None:
        result = await self.session.execute(
            select(Note).where(Note.material_id == material_id)
        )
        return result.scalar_one_or_none()
