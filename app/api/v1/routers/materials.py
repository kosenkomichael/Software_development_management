import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_session
from app.models.material import Material, MaterialStatus
from app.models.quiz import QuizStatus
from app.repositories.material_repository import MaterialRepository
from app.repositories.material_image_repository import MaterialImageRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.quiz_repository import QuizRepository
from app.schemas.material import MaterialListResponse, MaterialResponse
from app.schemas.note import NoteResponse, NoteStatusResponse
from app.schemas.quiz import (
    AnswerResponse,
    QuestionResponse,
    QuestionResult,
    QuizResponse,
    QuizStatusResponse,
    SubmitRequest,
    SubmitResponse,
)
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
    )


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")


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
        _storage.upload, data, str(current_user.id),
        file.filename or "upload", file.content_type or "",
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
    url = await run_in_threadpool(_storage.get_presigned_url, material.s3_key)
    return _to_material_response(material, url=url)


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

    questions = [
        QuestionResponse(
            id=str(q.id),
            text=q.text,
            question_type=q.question_type,
            order=q.order,
            answers=[AnswerResponse(id=str(a.id), text=a.text) for a in q.answers],
        )
        for q in sorted(quiz_with_q.questions, key=lambda x: x.order)
    ]
    return QuizResponse(id=str(quiz.id), material_id=material_id, status=quiz.status, questions=questions)


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

    quizzes = await QuizRepository(session).list_by_material(mid)
    if not quizzes or quizzes[0].status != QuizStatus.done:
        raise HTTPException(status_code=409, detail="Quiz is not ready")

    quiz = await QuizRepository(session).get_with_questions(quizzes[0].id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    q_map = {str(q.id): q for q in quiz.questions}
    results: list[QuestionResult] = []
    correct_count = 0

    for submitted in body.answers:
        question = q_map.get(submitted.question_id)
        if question is None:
            continue

        correct_ids = [str(a.id) for a in question.answers if a.is_correct]

        if question.question_type.value == "open":
            results.append(QuestionResult(
                question_id=submitted.question_id,
                is_correct=None,
                correct_ids=[],
            ))
            continue

        is_correct = set(submitted.selected_ids) == set(correct_ids)
        if is_correct:
            correct_count += 1

        explanation = next(
            (a.explanation for a in question.answers if a.is_correct and a.explanation), None
        )
        results.append(QuestionResult(
            question_id=submitted.question_id,
            is_correct=is_correct,
            correct_ids=correct_ids,
            explanation=explanation,
        ))

    scorable = sum(1 for r in results if r.is_correct is not None)
    score = round(correct_count / scorable, 2) if scorable else 0.0

    return SubmitResponse(
        score=score,
        total=len(results),
        correct=correct_count,
        results=results,
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

    data, mime = await run_in_threadpool(_storage.get_image, img.s3_key)
    return Response(
        content=data,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )
