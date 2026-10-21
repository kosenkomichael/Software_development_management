import json
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Answer, Question, QuestionType, Quiz, QuizStatus
from app.repositories.material_repository import MaterialRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.quiz_repository import QuizRepository
from app.services.llm.openai_client import OpenAICompatibleClient
from app.services.prompts import QUIZ_SYSTEM, QUIZ_USER


class _AnswerSchema(BaseModel):
    text: str
    is_correct: bool
    explanation: str | None = None


class _QuestionSchema(BaseModel):
    text: str
    type: QuestionType
    answers: list[_AnswerSchema] = []


class _QuizSchema(BaseModel):
    questions: list[_QuestionSchema]


class QuizService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._quiz_repo = QuizRepository(session)
        self._note_repo = NoteRepository(session)
        self._material_repo = MaterialRepository(session)
        self._llm = OpenAICompatibleClient()

    async def generate(self, material_id: UUID) -> Quiz:
        material = await self._material_repo.get_by_id(material_id)
        if material is None:
            raise ValueError(f"Material {material_id} not found")

        note = await self._note_repo.get_by_material(material_id)
        if note is None:
            raise ValueError("Notes must be generated before the quiz")

        quiz = Quiz(material_id=material_id, user_id=material.user_id, status=QuizStatus.processing)
        await self._quiz_repo.save(quiz)
        await self._session.flush()

        try:
            raw = await self._llm.complete(
                system=QUIZ_SYSTEM,
                user=QUIZ_USER.format(notes=note.content[:8000]),
            )
            parsed = _QuizSchema.model_validate(json.loads(raw))
            await self._save_questions(quiz, parsed)
            quiz.status = QuizStatus.done
            await self._session.commit()
            return quiz

        except Exception:
            quiz.status = QuizStatus.failed
            await self._session.commit()
            raise

    async def _save_questions(self, quiz: Quiz, data: _QuizSchema) -> None:
        for order, q in enumerate(data.questions, start=1):
            question = Question(
                quiz_id=quiz.id,
                text=q.text,
                question_type=q.type,
                order=order,
            )
            self._session.add(question)
            await self._session.flush()

            for a in q.answers:
                self._session.add(Answer(
                    question_id=question.id,
                    text=a.text,
                    is_correct=a.is_correct,
                    explanation=a.explanation,
                ))
        await self._session.flush()
