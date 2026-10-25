from uuid import UUID

from sqlalchemy import func, select

from app.models.material import Material
from app.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    async def list_by_user(self, user_id: UUID) -> list[Material]:
        result = await self.session.execute(
            select(Material).where(Material.user_id == user_id).order_by(Material.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_user_paginated(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Material], int]:
        count_result = await self.session.execute(
            select(func.count()).select_from(Material).where(Material.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Material)
            .where(Material.user_id == user_id)
            .order_by(Material.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total
