from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    model = Quiz

    async def get_with_questions(self, quiz_id: UUID) -> Quiz | None:
        result = await self.session.execute(
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions).selectinload(Quiz.questions.property.mapper.class_.answers))
        )
        return result.scalar_one_or_none()

    async def list_by_material(self, material_id: UUID) -> list[Quiz]:
        result = await self.session.execute(
            select(Quiz).where(Quiz.material_id == material_id)
        )
        return list(result.scalars().all())
