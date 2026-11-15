import re
import uuid
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from minio.error import S3Error
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_session
from app.models import Material, MaterialImage, MaterialStatus, Note, Quiz, QuizStatus, User
from app.repositories.material_repository import MaterialRepository
from app.schemas.public_material import (
    MaterialImportResponse,
    MaterialPublicationRequest,
    MaterialPublicationResponse,
    PublicMaterialDetail,
    PublicMaterialList,
    PublicMaterialSummary,
)
from app.services.material_import_service import import_material
from app.services.storage_service import StorageService

router = APIRouter(tags=["public materials"])
Session = Annotated[AsyncSession, Depends(get_session)]
storage = StorageService()


def parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(404, "Public material not found") from None


async def owned(value: str, user: User, session: AsyncSession) -> Material:
    material = await MaterialRepository(session).get_by_id(parse_id(value))
    if material is None or material.user_id != user.id:
        raise HTTPException(404, "Material not found")
    return material


async def available(value: str, session: AsyncSession, lock: bool = False) -> tuple[Material, User]:
    query = (
        select(Material, User)
        .join(User, User.id == Material.user_id)
        .where(
            Material.id == parse_id(value),
            Material.is_public.is_(True),
            Material.deleted_at.is_(None),
            Material.status == MaterialStatus.done,
            User.is_active.is_(True),
        )
    )
    if lock:
        query = query.with_for_update(of=Material)
    row = (await session.execute(query)).one_or_none()
    if row is None:
        raise HTTPException(404, "Public material not found")
    return row[0], row[1]


def summary(material: Material, user: User) -> PublicMaterialSummary:
    return PublicMaterialSummary(
        id=str(material.id),
        title=material.public_title or material.original_filename,
        author=" ".join(filter(None, [user.first_name, user.last_name])) or "Пользователь",
        published_at=material.published_at or material.created_at,
        size_bytes=material.size_bytes,
        has_quiz=material.published_quiz_id is not None,
    )


@router.get("/materials/{material_id}/publication", response_model=MaterialPublicationResponse)
async def publication(
    material_id: str, current_user: CurrentUser, session: Session
) -> MaterialPublicationResponse:
    material = await owned(material_id, current_user, session)
    return MaterialPublicationResponse(
        is_public=material.is_public,
        title=material.public_title or material.original_filename,
        has_quiz=material.published_quiz_id is not None,
    )


@router.patch("/materials/{material_id}/publication", response_model=MaterialPublicationResponse)
async def publish(
    material_id: str, body: MaterialPublicationRequest, current_user: CurrentUser, session: Session
) -> MaterialPublicationResponse:
    material = await owned(material_id, current_user, session)
    # Use the same lock as importing, so snapshots and their files stay consistent.
    material = await session.scalar(
        select(Material)
        .where(Material.id == material.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if material is None or material.deleted_at:
        raise HTTPException(404, "Material not found")
    title = (
        body.title
        if body.title is not None
        else material.public_title or material.original_filename
    ).strip()
    if not title:
        raise HTTPException(422, "Invalid material title")
    if body.is_public:
        note = await session.scalar(select(Note.id).where(Note.material_id == material.id))
        if material.status != MaterialStatus.done or note is None:
            raise HTTPException(409, "Notes not ready yet")
        quiz = await session.scalar(
            select(Quiz)
            .where(Quiz.material_id == material.id, Quiz.status == QuizStatus.done)
            .order_by(Quiz.created_at.desc(), Quiz.id.desc())
            .limit(1)
        )
        if material.published_quiz_id and (quiz is None or material.published_quiz_id != quiz.id):
            old = await session.get(Quiz, material.published_quiz_id)
            if old:
                old.is_public = False
        material.published_quiz_id = quiz.id if quiz else None
        if quiz:
            quiz.is_public = True
            quiz.public_title = quiz.public_title or title
            quiz.published_at = quiz.published_at or datetime.now(UTC)
        material.published_at = datetime.now(UTC)
    elif material.published_quiz_id:
        quiz = await session.get(Quiz, material.published_quiz_id)
        if quiz:
            quiz.is_public = False
        material.published_quiz_id = None
    material.is_public = body.is_public
    material.public_title = title
    await session.commit()
    return MaterialPublicationResponse(
        is_public=material.is_public, title=title, has_quiz=material.published_quiz_id is not None
    )


@router.get("/public-materials", response_model=PublicMaterialList)
async def public_list(
    current_user: CurrentUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
) -> PublicMaterialList:
    query = (
        select(Material, User)
        .join(User, User.id == Material.user_id)
        .where(
            Material.is_public.is_(True),
            Material.deleted_at.is_(None),
            Material.status == MaterialStatus.done,
            User.is_active.is_(True),
            exists().where(Note.material_id == Material.id),
        )
    )
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.execute(
        query.order_by(Material.published_at.desc(), Material.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return PublicMaterialList(
        items=[summary(material, user) for material, user in rows], total=total or 0
    )


@router.get("/public-materials/{material_id}", response_model=PublicMaterialDetail)
async def public_detail(
    material_id: str, current_user: CurrentUser, session: Session, response: Response
) -> PublicMaterialDetail:
    material, user = await available(material_id, session)
    note = await session.scalar(select(Note).where(Note.material_id == material.id))
    if note is None:
        raise HTTPException(409, "Notes not ready yet")
    response.headers["Cache-Control"] = "no-store"
    return PublicMaterialDetail(
        **summary(material, user).model_dump(),
        filename=material.original_filename,
        content_type=material.content_type,
        note_content=note.content,
        quiz_id=str(material.published_quiz_id) if material.published_quiz_id else None,
    )


@router.get("/public-materials/{material_id}/download")
async def download(material_id: str, current_user: CurrentUser, session: Session) -> Response:
    material, _ = await available(material_id, session)
    try:
        data, _ = await run_in_threadpool(storage.get_object, material.s3_key)
    except S3Error:
        raise HTTPException(404, "Material not found") from None
    encoded_filename = quote(material.original_filename, safe="")
    filename = re.sub(r"[^\x20-\x7e]", "_", material.original_filename).replace('"', "'")
    return Response(
        data,
        media_type=material.content_type,
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"
            ),
        },
    )


@router.get("/public-materials/{material_id}/images/{order}")
async def image(
    material_id: str, order: int, current_user: CurrentUser, session: Session
) -> Response:
    material, _ = await available(material_id, session)
    item = await session.scalar(
        select(MaterialImage).where(
            MaterialImage.material_id == material.id, MaterialImage.order == order
        )
    )
    if item is None:
        raise HTTPException(404, "Material not found")
    try:
        data, mime = await run_in_threadpool(storage.get_object, item.s3_key)
    except S3Error:
        raise HTTPException(404, "Material not found") from None
    return Response(data, media_type=mime, headers={"Cache-Control": "no-store"})


@router.post(
    "/public-materials/{material_id}/import", response_model=MaterialImportResponse, status_code=201
)
async def import_package(
    material_id: str, current_user: CurrentUser, session: Session, response: Response
) -> MaterialImportResponse:
    material, _ = await available(material_id, session, lock=True)
    result, created = await import_material(material, current_user, session, storage)
    response.status_code = 201 if created else 200
    return MaterialImportResponse(material_id=str(result.id), imported=created)
