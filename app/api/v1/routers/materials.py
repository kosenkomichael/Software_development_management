from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_session
from app.models.material import Material
from app.repositories.material_repository import MaterialRepository
from app.schemas.material import MaterialListResponse, MaterialResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/materials", tags=["materials"])

_storage = StorageService()


def _to_response(material: Material, url: str | None = None) -> MaterialResponse:
    return MaterialResponse(
        id=str(material.id),
        original_filename=material.original_filename,
        content_type=material.content_type,
        size_bytes=material.size_bytes,
        status=material.status,
        created_at=material.created_at,
        download_url=url,
    )


@router.post("/upload", response_model=MaterialResponse, status_code=201)
async def upload_material(
    file: UploadFile,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialResponse:
    if not StorageService.allowed_content_type(file.content_type or ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: PDF, DOCX, PPTX",
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
        file.content_type or "application/octet-stream",
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

    return _to_response(material)


@router.get("/", response_model=MaterialListResponse)
async def list_materials(
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialListResponse:
    repo = MaterialRepository(session)
    materials = await repo.list_by_user(current_user.id)
    items = [_to_response(m) for m in materials]
    return MaterialListResponse(items=items, total=len(items))


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MaterialResponse:
    import uuid

    try:
        mid = uuid.UUID(material_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    repo = MaterialRepository(session)
    material = await repo.get_by_id(mid)

    if material is None or material.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    url = await run_in_threadpool(_storage.get_presigned_url, material.s3_key)
    return _to_response(material, url=url)
