import logging
import uuid
from pathlib import PurePosixPath

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Answer,
    Material,
    MaterialImage,
    MaterialStatus,
    Note,
    Question,
    Quiz,
    QuizStatus,
    User,
)
from app.repositories.quiz_repository import QuizRepository
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


async def import_material(
    source: Material, participant: User, session: AsyncSession, storage: StorageService
) -> tuple[Material, bool]:
    # The source row is locked, serializing imports and publication changes.
    if source.user_id == participant.id:
        return source, False
    existing = await session.scalar(
        select(Material).where(
            Material.user_id == participant.id,
            Material.source_material_id == source.id,
            Material.deleted_at.is_(None),
        )
    )
    if existing:
        return existing, False
    note = await session.scalar(select(Note).where(Note.material_id == source.id))
    if note is None:
        raise HTTPException(409, "Notes not ready yet")
    owner = await session.get(User, source.user_id)
    author = " ".join(filter(None, [owner.first_name, owner.last_name])) if owner else ""
    mid = uuid.uuid4()
    file_key = f"{participant.id}/{uuid.uuid4()}{PurePosixPath(source.s3_key).suffix}"
    material = Material(
        id=mid,
        user_id=participant.id,
        original_filename=source.original_filename,
        s3_key=file_key,
        content_type=source.content_type,
        size_bytes=source.size_bytes,
        status=MaterialStatus.done,
        source_material_id=source.id,
        source_author=author or "Пользователь",
    )
    copied = []
    try:
        copied.append(file_key)
        await run_in_threadpool(storage.copy_object, source.s3_key, file_key)
        session.add(material)
        await session.flush()
        session.add(
            Note(
                material_id=mid,
                user_id=participant.id,
                content=note.content.replace(
                    f"/api/v1/materials/{source.id}/images/", f"/api/v1/materials/{mid}/images/"
                ),
                llm_model=note.llm_model,
                generation_time_ms=note.generation_time_ms,
                validation_score=note.validation_score,
            )
        )
        images = await session.scalars(
            select(MaterialImage)
            .where(MaterialImage.material_id == source.id)
            .order_by(MaterialImage.order)
        )
        for image in images:
            key = f"images/{mid}/{image.order}{PurePosixPath(image.s3_key).suffix}"
            copied.append(key)
            await run_in_threadpool(storage.copy_object, image.s3_key, key)
            session.add(
                MaterialImage(
                    material_id=mid,
                    user_id=participant.id,
                    order=image.order,
                    s3_key=key,
                    mime_type=image.mime_type,
                )
            )
        quiz = (
            await QuizRepository(session).get_with_questions(source.published_quiz_id)
            if source.published_quiz_id
            else None
        )
        if quiz and quiz.status == QuizStatus.done and quiz.material_id == source.id:
            clone = Quiz(material_id=mid, user_id=participant.id, status=QuizStatus.done)
            session.add(clone)
            await session.flush()
            for question in sorted(quiz.questions, key=lambda q: q.order):
                q = Question(
                    quiz_id=clone.id,
                    text=question.text,
                    question_type=question.question_type,
                    order=question.order,
                )
                session.add(q)
                await session.flush()
                for answer in question.answers:
                    session.add(
                        Answer(
                            question_id=q.id,
                            text=answer.text,
                            is_correct=answer.is_correct,
                            explanation=answer.explanation,
                        )
                    )
        await session.commit()
        return material, True
    except Exception:
        await session.rollback()
        for key in copied:
            try:
                await run_in_threadpool(storage.delete, key)
            except Exception:
                logger.warning("Could not clean up an incomplete material import")
        raise HTTPException(503, "Material import failed") from None
