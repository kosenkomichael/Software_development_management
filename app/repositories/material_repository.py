from uuid import UUID

from sqlalchemy import select

from app.models.material import Material
from app.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    async def list_by_user(self, user_id: UUID) -> list[Material]:
        result = await self.session.execute(
            select(Material).where(Material.user_id == user_id).order_by(Material.created_at.desc())
        )
        return list(result.scalars().all())
