from uuid import UUID

from sqlalchemy import func, select

from app.models.material import Material
from app.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    async def get_by_id(self, id: UUID) -> Material | None:
        return await self.session.scalar(
            select(Material).where(Material.id == id, Material.deleted_at.is_(None))
        )

    async def list_by_user(self, user_id: UUID) -> list[Material]:
        result = await self.session.execute(
            select(Material)
            .where(Material.user_id == user_id, Material.deleted_at.is_(None))
            .order_by(Material.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_user_paginated(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Material], int]:
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Material)
            .where(Material.user_id == user_id, Material.deleted_at.is_(None))
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Material)
            .where(Material.user_id == user_id, Material.deleted_at.is_(None))
            .order_by(Material.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total
