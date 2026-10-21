import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material, MaterialStatus
from app.models.note import Note
from app.repositories.material_repository import MaterialRepository
from app.repositories.note_repository import NoteRepository
from app.services.llm.openai_client import OpenAICompatibleClient
from app.services.prompts import NOTES_SYSTEM, NOTES_USER
from app.services.storage_service import StorageService
from app.services.text_extractor import extract_text


class NotesService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._note_repo = NoteRepository(session)
        self._material_repo = MaterialRepository(session)
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
            text = extract_text(file_data, material.content_type)

            if not text.strip():
                raise ValueError("No text could be extracted from the file")

            t0 = time.monotonic()
            content = await self._llm.complete(
                system=NOTES_SYSTEM,
                user=NOTES_USER.format(text=text[:12000]),
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)

            from app.core.config import settings
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
            material.status = MaterialStatus.failed
            await self._session.commit()
            raise

    async def _download(self, material: Material) -> bytes:
        from fastapi.concurrency import run_in_threadpool
        url = await run_in_threadpool(self._storage.get_presigned_url, material.s3_key)

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
