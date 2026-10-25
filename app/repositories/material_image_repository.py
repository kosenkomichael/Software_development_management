import uuid
from typing import Any

from sqlalchemy import delete, select

from app.models.material_image import MaterialImage
from app.repositories.base import BaseRepository


class MaterialImageRepository(BaseRepository[MaterialImage]):
    model = MaterialImage

    async def list_by_material(self, material_id: uuid.UUID) -> list[MaterialImage]:
        result = await self.session.execute(
            select(MaterialImage)
            .where(MaterialImage.material_id == material_id)
            .order_by(MaterialImage.order)
        )
        return list(result.scalars().all())

    async def get_by_material_and_order(self, material_id: uuid.UUID, order: int) -> MaterialImage | None:
        result = await self.session.execute(
            select(MaterialImage).where(
                MaterialImage.material_id == material_id,
                MaterialImage.order == order,
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_material(self, material_id: uuid.UUID) -> Any:
        result = await self.session.execute(
            delete(MaterialImage).where(MaterialImage.material_id == material_id)
        )
        return result
