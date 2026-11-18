import random
import re
import uuid
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from minio.error import S3Error
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.jwt import create_download_token, decode_download_token
from app.db.session import get_session
from app.models.material import Material, MaterialStatus
from app.models.quiz import QuizStatus
from app.models.quiz_attempt import QuizAttempt
from app.repositories.material_image_repository import MaterialImageRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.quiz_repository import QuizRepository
from app.schemas.material import MaterialListResponse, MaterialResponse, MaterialUpdateRequest
from app.schemas.note import NoteResponse, NoteStatusResponse
from app.schemas.quiz import (
    AnswerResponse,
    AttemptDetail,
    AttemptListResponse,
    AttemptSummary,
    QuestionResponse,
    QuizResponse,
    QuizStatusResponse,
    SubmitRequest,
    SubmitResponse,
)
from app.services.quiz_grading import grade_quiz
from app.services.storage_service import StorageService

router = APIRouter(prefix="/materials", tags=["materials"])

_storage = StorageService()


def _to_material_response(material: Material, url: str | None = None) -> MaterialResponse:
    return MaterialResponse(
        id=str(material.id),
        original_filename=material.original_filename,
        content_type=material.content_type,
        size_bytes=material.size_bytes,
        status=material.status,
        created_at=material.created_at,
        download_url=url,
        is_favorite=material.is_favorite,
        source_author=material.source_author,
    )


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found") from None


# ─── Materials ────────────────────────────────────────────────────────────────


@router.post("/upload", response_model=MaterialResponse, status_code=201)
async def upload_material(
    file: UploadFile,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialResponse:
    if not StorageService.allowed_content_type(file.content_type or ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Allowed: PDF, DOCX, PPTX",
        )

    data = await file.read()
    if len(data) > StorageService.max_size():
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum allowed size of 50 MB",
        )

    s3_key = await run_in_threadpool(
        _storage.upload,
        data,
        str(current_user.id),
        file.filename or "upload",
        file.content_type or "",
    )

    material = Material(
        user_id=current_user.id,
        original_filename=file.filename or "upload",
        s3_key=s3_key,
        content_type=file.content_type or "",
        size_bytes=len(data),
    )
    repo = MaterialRepository(session)
    await repo.save(material)
    await session.commit()

    # Queue note generation after upload
    from app.workers.tasks import generate_notes_task

    generate_notes_task.delay(str(material.id))

    return _to_material_response(material)


@router.get("/", response_model=MaterialListResponse)
async def list_materials(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MaterialListResponse:
    offset = (page - 1) * page_size
    materials, total = await MaterialRepository(session).list_by_user_paginated(
        current_user.id, limit=page_size, offset=offset
    )
    return MaterialListResponse(items=[_to_material_response(m) for m in materials], total=total)


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")
    token = create_download_token(str(current_user.id), str(material.id))
    url = f"/api/v1/materials/{material.id}/download?token={token}"
    return _to_material_response(material, url=url)


@router.patch("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: str,
    body: MaterialUpdateRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialResponse:
    material = await MaterialRepository(session).get_by_id(_parse_uuid(material_id))
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")
    if body.original_filename is not None:
        material.original_filename = body.original_filename
    if body.is_favorite is not None:
        material.is_favorite = body.is_favorite
    await session.commit()
    return _to_material_response(material)


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    material = await MaterialRepository(session).get_by_id(_parse_uuid(material_id))
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")
    material.deleted_at = datetime.now(UTC)
    await session.commit()


@router.get("/{material_id}/download")
async def download_material(
    material_id: str,
    token: Annotated[str, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    mid = _parse_uuid(material_id)
    invalid = HTTPException(
        status_code=401,
        detail="Ссылка на скачивание недействительна или истекла",
    )
    payload = decode_download_token(token)
    if payload is None or payload.get("mid") != str(mid):
        raise invalid
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or str(material.user_id) != payload.get("sub"):
        raise HTTPException(status_code=404, detail="Material not found")
    try:
        data, mime = await run_in_threadpool(_storage.get_object, material.s3_key)
    except S3Error:
        raise HTTPException(status_code=404, detail="Material not found") from None
    ascii_fallback = re.sub(r"[^\x20-\x7e]", "_", material.original_filename).replace('"', "'")
    disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(material.original_filename, safe='')}"
    )
    return Response(
        content=data,
        media_type=material.content_type or "application/octet-stream",
        headers={"Content-Disposition": disposition, "Cache-Control": "no-store"},
    )


# ─── Notes ────────────────────────────────────────────────────────────────────


@router.get("/{material_id}/notes/status", response_model=NoteStatusResponse)
async def notes_status(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteStatusResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    note = await NoteRepository(session).get_by_material(mid)
    return NoteStatusResponse(
        material_id=material_id,
        status=material.status,
        note_id=str(note.id) if note else None,
    )


@router.get("/{material_id}/notes", response_model=NoteResponse)
async def get_notes(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    note = await NoteRepository(session).get_by_material(mid)
    if note is None:
        raise HTTPException(status_code=404, detail="Notes not ready yet")

    return NoteResponse(
        id=str(note.id),
        material_id=str(note.material_id),
        content=note.content,
        llm_model=note.llm_model,
        generation_time_ms=note.generation_time_ms,
        created_at=note.created_at,
    )


@router.post("/{material_id}/notes/regenerate", response_model=NoteStatusResponse, status_code=202)
async def regenerate_notes(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteStatusResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.status == MaterialStatus.processing:
        raise HTTPException(status_code=409, detail="Generation already in progress")

    note = await NoteRepository(session).get_by_material(mid)
    if note is not None:
        await NoteRepository(session).delete(note)

    material.status = MaterialStatus.uploaded
    await session.commit()

    from app.workers.tasks import generate_notes_task

    generate_notes_task.delay(str(mid))

    return NoteStatusResponse(material_id=material_id, status=MaterialStatus.uploaded, note_id=None)


# ─── Quiz ─────────────────────────────────────────────────────────────────────


@router.post("/{material_id}/quiz/generate", response_model=QuizStatusResponse, status_code=202)
async def generate_quiz(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizStatusResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    note = await NoteRepository(session).get_by_material(mid)
    if note is None:
        raise HTTPException(status_code=409, detail="Generate notes first")

    from app.workers.tasks import generate_quiz_task

    generate_quiz_task.delay(str(mid))

    return QuizStatusResponse(material_id=material_id, status=QuizStatus.processing)


@router.get("/{material_id}/quiz/status", response_model=QuizStatusResponse)
async def quiz_status(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuizStatusResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    quizzes = await QuizRepository(session).list_by_material(mid)
    latest = quizzes[0] if quizzes else None
    return QuizStatusResponse(
        material_id=material_id,
        status=latest.status if latest else QuizStatus.processing,
        quiz_id=str(latest.id) if latest else None,
    )


@router.get("/{material_id}/quiz", response_model=QuizResponse)
async def get_quiz(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    response: Response,
) -> QuizResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    quizzes = await QuizRepository(session).list_by_material(mid)
    if not quizzes:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz = quizzes[0]
    if quiz.status != QuizStatus.done:
        raise HTTPException(status_code=409, detail="Quiz is not ready yet")

    quiz_with_q = await QuizRepository(session).get_with_questions(quiz.id)
    if quiz_with_q is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = []
    for q in sorted(quiz_with_q.questions, key=lambda x: x.order):
        answers = [AnswerResponse(id=str(a.id), text=a.text) for a in q.answers]
        random.shuffle(answers)
        questions.append(
            QuestionResponse(
                id=str(q.id),
                text=q.text,
                question_type=q.question_type,
                order=q.order,
                answers=answers,
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return QuizResponse(
        id=str(quiz.id), material_id=material_id, status=quiz.status, questions=questions
    )


@router.post("/{material_id}/quiz/submit", response_model=SubmitResponse)
async def submit_quiz(
    material_id: str,
    body: SubmitRequest,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SubmitResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    repo = QuizRepository(session)
    if body.quiz_id is not None:
        quiz = await repo.get_with_questions(body.quiz_id)
    else:
        quizzes = await repo.list_by_material(mid)
        quiz = await repo.get_with_questions(quizzes[0].id) if quizzes else None
    if quiz is None or quiz.material_id != mid or quiz.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.status != QuizStatus.done:
        raise HTTPException(status_code=409, detail="Quiz is not ready yet")

    result, snapshot = grade_quiz(quiz, body.answers)
    attempt = QuizAttempt(
        user_id=current_user.id,
        material_id=mid,
        quiz_id=quiz.id,
        score=result.score,
        total=result.total,
        correct=result.correct,
        quiz_snapshot=snapshot.model_dump(mode="json"),
        answers=[answer.model_dump(mode="json") for answer in body.answers],
        results=[item.model_dump(mode="json") for item in result.results],
    )
    session.add(attempt)
    await session.commit()
    result.attempt_id = str(attempt.id)
    return result


def _attempt_summary(attempt: QuizAttempt) -> AttemptSummary:
    return AttemptSummary(
        id=str(attempt.id),
        quiz_id=str(attempt.quiz_id) if attempt.quiz_id else None,
        created_at=attempt.created_at,
        duration_ms=attempt.duration_ms,
        score=attempt.score,
        total=attempt.total,
        correct=attempt.correct,
    )


@router.get("/{material_id}/quiz/attempts", response_model=AttemptListResponse)
async def list_quiz_attempts(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    response: Response,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> AttemptListResponse:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")
    filters = (QuizAttempt.material_id == mid, QuizAttempt.user_id == current_user.id)
    total = await session.scalar(select(func.count()).select_from(QuizAttempt).where(*filters))
    rows = await session.scalars(
        select(QuizAttempt)
        .where(*filters)
        .order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    response.headers["Cache-Control"] = "no-store"
    return AttemptListResponse(items=[_attempt_summary(row) for row in rows], total=total or 0)


@router.get("/{material_id}/quiz/attempts/{attempt_id}", response_model=AttemptDetail)
async def get_quiz_attempt(
    material_id: str,
    attempt_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    response: Response,
) -> AttemptDetail:
    material = await MaterialRepository(session).get_by_id(_parse_uuid(material_id))
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")
    attempt = await session.scalar(
        select(QuizAttempt).where(
            QuizAttempt.id == _parse_uuid(attempt_id),
            QuizAttempt.material_id == _parse_uuid(material_id),
            QuizAttempt.user_id == current_user.id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    response.headers["Cache-Control"] = "no-store"
    return AttemptDetail(
        **_attempt_summary(attempt).model_dump(),
        quiz=attempt.quiz_snapshot,
        answers=attempt.answers,
        result=SubmitResponse(
            attempt_id=str(attempt.id),
            duration_ms=attempt.duration_ms,
            score=attempt.score,
            total=attempt.total,
            correct=attempt.correct,
            results=attempt.results,
        ),
    )


@router.get("/{material_id}/images/{order}")
async def get_material_image(
    material_id: str,
    order: int,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    mid = _parse_uuid(material_id)
    material = await MaterialRepository(session).get_by_id(mid)
    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Material not found")

    img = await MaterialImageRepository(session).get_by_material_and_order(mid, order)
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")

    data, mime = await run_in_threadpool(_storage.get_object, img.s3_key)
    return Response(
        content=data,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )
