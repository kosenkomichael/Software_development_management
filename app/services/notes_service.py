import re
import time
from uuid import UUID

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.material import Material, MaterialStatus
from app.models.material_image import MaterialImage
from app.models.note import Note
from app.repositories.material_image_repository import MaterialImageRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.note_repository import NoteRepository
from app.services.content_parts import image_url_part, pdf_file_part
from app.services.llm.openai_client import OpenAICompatibleClient
from app.services.prompts import NOTES_SYSTEM, NOTES_USER
from app.services.storage_service import StorageService
from app.services.text_extractor import extract_images, extract_text

_IMAGE_N_RE = re.compile(r"\[IMAGE_(\d+)\]")


class NotesService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._note_repo = NoteRepository(session)
        self._material_repo = MaterialRepository(session)
        self._image_repo = MaterialImageRepository(session)
        self._storage = StorageService()
        self._llm = OpenAICompatibleClient()

    async def generate(self, material_id: UUID) -> Note:
        material = await self._material_repo.get_by_id(material_id)
        if material is None:
            raise ValueError(f"Material {material_id} not found")

        existing = await self._note_repo.get_by_material(material_id)
        if existing is not None:
            return existing

        material.status = MaterialStatus.processing
        await self._session.flush()

        try:
            file_data = await self._download(material)

            images = extract_images(file_data, material.content_type)

            # Regeneration must be idempotent: drop previous images first.
            await self._image_repo.delete_by_material(material_id)
            await run_in_threadpool(
                self._storage.delete_prefix, f"images/{material_id}/"
            )

            image_rows: list[MaterialImage] = []
            for i, (data, mime) in enumerate(images, start=1):
                s3_key = await run_in_threadpool(
                    self._storage.upload_image, data, str(material_id), i, mime
                )
                row = MaterialImage(
                    material_id=material_id,
                    user_id=material.user_id,
                    order=i,
                    s3_key=s3_key,
                    mime_type=mime,
                )
                self._session.add(row)
                image_rows.append(row)
            await self._session.flush()

            if material.content_type == "application/pdf":
                text = ""
                file_parts = [pdf_file_part(material.original_filename, file_data)]
            else:
                text = extract_text(file_data, material.content_type)
                if not text.strip():
                    raise ValueError("No text could be extracted from the file")
                file_parts = [
                    image_url_part(data, mime)
                    for data, mime in images[: settings.max_images_per_request]
                ]

            images_note = (
                f"The source contains {len(images)} image(s), numbered [IMAGE_1]"
                + (f" to [IMAGE_{len(images)}]" if len(images) > 1 else "")
                + " in document order. Embed each as instructed."
                if images
                else ""
            )

            t0 = time.monotonic()
            content = await self._llm.complete(
                system=NOTES_SYSTEM,
                user=NOTES_USER.format(text=text[:12000], images_note=images_note),
                file_parts=file_parts,
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)

            content = _substitute_images(content, material_id, len(images))

            note = Note(
                material_id=material_id,
                user_id=material.user_id,
                content=content,
                llm_model=settings.llm_model,
                generation_time_ms=elapsed_ms,
            )
            await self._note_repo.save(note)
            material.status = MaterialStatus.done
            await self._session.commit()
            return note

        except Exception:
            # Flushed MaterialImage rows are discarded by the implicit rollback
            # in the failed-status commit path; just clean up MinIO objects.
            await run_in_threadpool(
                self._storage.delete_prefix, f"images/{material_id}/"
            )
            material.status = MaterialStatus.failed
            await self._session.commit()
            raise

    async def _download(self, material: Material) -> bytes:
        url = await run_in_threadpool(self._storage.get_presigned_url, material.s3_key)

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content


def _substitute_images(content: str, material_id: UUID, image_count: int) -> str:
    """Replace [IMAGE_N] labels with markdown links to the image endpoint."""
    def _repl(match: re.Match[str]) -> str:
        n = int(match.group(1))
        if not 1 <= n <= image_count:
            return match.group(0)
        return f"![Рисунок {n}](/api/v1/materials/{material_id}/images/{n})"

    return _IMAGE_N_RE.sub(_repl, content)
