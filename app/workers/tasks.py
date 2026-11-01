import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.services.notes_service import NotesService
from app.services.quiz_service import QuizService
from app.workers.celery_app import celery_app


async def _generate(service_cls: type[NotesService] | type[QuizService], material_id: str) -> None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            await service_cls(session).generate(uuid.UUID(material_id))
    finally:
        await engine.dispose()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_notes_task(self, material_id: str) -> None:
    try:
        asyncio.run(_generate(NotesService, material_id))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def generate_quiz_task(self, material_id: str) -> None:
    try:
        asyncio.run(_generate(QuizService, material_id))
    except Exception as exc:
        raise self.retry(exc=exc)
