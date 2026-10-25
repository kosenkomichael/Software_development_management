import asyncio
import uuid

from app.db.session import async_session_factory
from app.services.notes_service import NotesService
from app.services.quiz_service import QuizService
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_notes_task(self, material_id: str) -> None:
    async def _run() -> None:
        async with async_session_factory() as session:
            await NotesService(session).generate(uuid.UUID(material_id))

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_quiz_task(self, material_id: str) -> None:
    async def _run() -> None:
        async with async_session_factory() as session:
            await QuizService(session).generate(uuid.UUID(material_id))

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
