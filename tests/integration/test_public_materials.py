"""Real database and MinIO checks for publishing and importing complete packages."""

import asyncio
import base64
import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete, select

from app.db.session import async_session_factory
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
from app.models.quiz import QuestionType
from app.repositories.quiz_repository import QuizRepository
from app.services.storage_service import StorageService


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API and MinIO")
class PublicMaterialTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_package_and_independent_import(self):
        users, tokens, headers, keys = [], [], [], set()
        storage = StorageService()
        source_bytes = b"%PDF-1.4\nPublic package integration test"
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWZkAAAAASUVORK5CYII="
        )
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=30) as client:
            try:
                for _ in range(3):
                    credentials = {
                        "email": f"package-{uuid.uuid4().hex}@example.com",
                        "password": secrets.token_urlsafe(20),
                    }
                    response = await client.post("/auth/register", json=credentials)
                    response.raise_for_status()
                    users.append(uuid.UUID(response.json()["id"]))
                    response = await client.post("/auth/login", json=credentials)
                    response.raise_for_status()
                    tokens.append(response.json())
                    headers.append({"Authorization": "Bearer " + response.json()["access_token"]})
                key = storage.upload(source_bytes, str(users[0]), "lecture.pdf", "application/pdf")
                keys.add(key)
                async with async_session_factory() as session:
                    material = Material(
                        user_id=users[0],
                        original_filename="lecture.pdf",
                        s3_key=key,
                        content_type="application/pdf",
                        size_bytes=len(source_bytes),
                        status=MaterialStatus.done,
                    )
                    session.add(material)
                    await session.flush()
                    mid = str(material.id)
                    image_key = storage.upload_image(png, mid, 1, "image/png")
                    keys.add(image_key)
                    session.add(
                        MaterialImage(
                            user_id=users[0],
                            material_id=material.id,
                            order=1,
                            s3_key=image_key,
                            mime_type="image/png",
                        )
                    )
                    session.add(
                        Note(
                            user_id=users[0],
                            material_id=material.id,
                            content=f"## Lecture\n![Picture](/api/v1/materials/{mid}/images/1)",
                            llm_model="fixture",
                            generation_time_ms=0,
                        )
                    )
                    quiz = Quiz(user_id=users[0], material_id=material.id, status=QuizStatus.done)
                    session.add(quiz)
                    await session.flush()
                    qid = str(quiz.id)
                    question = Question(
                        quiz_id=quiz.id, text="Question", question_type=QuestionType.single, order=1
                    )
                    session.add(question)
                    await session.flush()
                    answer = Answer(
                        question_id=question.id, text="Yes", is_correct=True, explanation="Because"
                    )
                    session.add_all(
                        [answer, Answer(question_id=question.id, text="No", is_correct=False)]
                    )
                    await session.flush()
                    source_answer = {
                        "question_id": str(question.id),
                        "selected_ids": [str(answer.id)],
                    }
                    await session.commit()
                public = f"/public-materials/{mid}"
                response = await client.get(public, headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.patch(
                    f"/materials/{mid}/publication", headers=headers[1], json={"is_public": True}
                )
                self.assertEqual(response.status_code, 404)
                response = await client.patch(
                    f"/materials/{mid}/publication",
                    headers=headers[0],
                    json={"is_public": True, "title": "Complete package"},
                )
                response.raise_for_status()
                self.assertTrue(response.json()["has_quiz"])
                response = await client.get("/public-materials", headers=headers[1])
                response.raise_for_status()
                self.assertIn(mid, [item["id"] for item in response.json()["items"]])
                response = await client.get(public, headers=headers[1])
                response.raise_for_status()
                self.assertEqual(response.json()["quiz_id"], qid)
                self.assertIn("Lecture", response.json()["note_content"])
                response = await client.get(public + "/download", headers=headers[1])
                self.assertEqual(response.content, source_bytes)
                response = await client.get(public + "/images/1", headers=headers[1])
                self.assertEqual(response.content, png)
                response = await client.get(f"/materials/{mid}/notes", headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.post(
                    f"/public-quizzes/{qid}/submit",
                    headers=headers[1],
                    json={"answers": [source_answer]},
                )
                response.raise_for_status()
                # Concurrent retries must create a single independent copy.
                imports = await asyncio.gather(
                    *[client.post(public + "/import", headers=headers[1]) for _ in range(2)]
                )
                self.assertEqual(sorted(r.status_code for r in imports), [200, 201])
                copy_id = imports[0].json()["material_id"]
                self.assertEqual(copy_id, imports[1].json()["material_id"])
                async with async_session_factory() as session:
                    copied = await session.get(Material, uuid.UUID(copy_id))
                    keys.add(copied.s3_key)
                    self.assertNotEqual(copied.s3_key, key)
                    self.assertFalse(copied.is_public)
                    self.assertFalse(copied.is_favorite)
                    copied_quiz = await session.scalar(
                        select(Quiz).where(Quiz.material_id == copied.id)
                    )
                    self.assertIsNotNone(copied_quiz)
                    self.assertNotEqual(copied_quiz.id, quiz.id)
                    self.assertFalse(copied_quiz.is_public)
                    copied_quiz = await QuizRepository(session).get_with_questions(copied_quiz.id)
                    self.assertNotEqual(copied_quiz.questions[0].id, question.id)
                    self.assertEqual(
                        {
                            answer.text: answer.is_correct
                            for answer in copied_quiz.questions[0].answers
                        },
                        {"Yes": True, "No": False},
                    )
                    note = await session.scalar(select(Note).where(Note.material_id == copied.id))
                    self.assertIn(f"/materials/{copy_id}/images/1", note.content)
                    self.assertNotIn(mid, note.content)
                    image = await session.scalar(
                        select(MaterialImage).where(MaterialImage.material_id == copied.id)
                    )
                    keys.add(image.s3_key)
                    self.assertNotEqual(image.s3_key, image_key)
                response = await client.get(
                    f"/materials/{copy_id}/quiz/attempts", headers=headers[1]
                )
                self.assertEqual(response.json()["total"], 0)
                response = await client.post(public + "/import", headers=headers[0])
                self.assertEqual(response.json()["material_id"], mid)
                # A failed copy must not create a half-imported material.
                storage.delete(image_key)
                response = await client.post(public + "/import", headers=headers[2])
                self.assertEqual(response.status_code, 503)
                response = await client.get("/materials/", headers=headers[2])
                self.assertEqual(response.json()["total"], 0)
                response = await client.patch(
                    f"/materials/{mid}/publication", headers=headers[0], json={"is_public": False}
                )
                response.raise_for_status()
                for suffix in ["", "/download", "/images/1"]:
                    response = await client.get(public + suffix, headers=headers[1])
                    self.assertEqual(response.status_code, 404)
                response = await client.post(public + "/import", headers=headers[2])
                self.assertEqual(response.status_code, 404)
                response = await client.get(f"/public-quizzes/{qid}", headers=headers[1])
                self.assertEqual(response.status_code, 404)
                async with async_session_factory() as session:
                    await session.execute(delete(Material).where(Material.id == uuid.UUID(mid)))
                    await session.commit()
                storage.delete(key)
                response = await client.get(f"/materials/{copy_id}", headers=headers[1])
                response.raise_for_status()
                response = await client.get(
                    "http://127.0.0.1:8000" + response.json()["download_url"]
                )
                self.assertEqual(response.content, source_bytes)
                response = await client.get(f"/materials/{copy_id}/images/1", headers=headers[1])
                self.assertEqual(response.content, png)
                response = await client.get(f"/materials/{copy_id}/quiz", headers=headers[1])
                response.raise_for_status()
                self.assertEqual(len(response.json()["questions"]), 1)
                response = await client.get("/public-quizzes/attempts", headers=headers[1])
                self.assertEqual(response.json()["total"], 1)
                # A lecture with notes can be shared without generating a test.
                extra_key = storage.upload(
                    source_bytes, str(users[0]), "notes-only.pdf", "application/pdf"
                )
                keys.add(extra_key)
                async with async_session_factory() as session:
                    extra = Material(
                        user_id=users[0],
                        original_filename="notes-only.pdf",
                        s3_key=extra_key,
                        content_type="application/pdf",
                        size_bytes=len(source_bytes),
                        status=MaterialStatus.uploaded,
                    )
                    session.add(extra)
                    await session.commit()
                    extra_id = str(extra.id)
                response = await client.patch(
                    f"/materials/{extra_id}/publication",
                    headers=headers[0],
                    json={"is_public": True},
                )
                self.assertEqual(response.status_code, 409)
                async with async_session_factory() as session:
                    extra = await session.get(Material, uuid.UUID(extra_id))
                    extra.status = MaterialStatus.done
                    session.add(
                        Note(
                            user_id=users[0],
                            material_id=extra.id,
                            content="Ready notes without a quiz",
                            llm_model="fixture",
                            generation_time_ms=0,
                        )
                    )
                    await session.commit()
                response = await client.patch(
                    f"/materials/{extra_id}/publication",
                    headers=headers[0],
                    json={"is_public": True},
                )
                response.raise_for_status()
                self.assertFalse(response.json()["has_quiz"])
                response = await client.get(f"/public-materials/{extra_id}", headers=headers[1])
                self.assertIsNone(response.json()["quiz_id"])
                response = await client.post(
                    f"/public-materials/{extra_id}/import", headers=headers[1]
                )
                response.raise_for_status()
                extra_copy_id = response.json()["material_id"]
                response = await client.get(
                    f"/materials/{extra_copy_id}/quiz/status", headers=headers[1]
                )
                self.assertIsNone(response.json()["quiz_id"])
                response = await client.delete(f"/materials/{extra_copy_id}", headers=headers[1])
                self.assertEqual(response.status_code, 204)
                response = await client.post(
                    f"/public-materials/{extra_id}/import", headers=headers[1]
                )
                response.raise_for_status()
                self.assertNotEqual(response.json()["material_id"], extra_copy_id)
            finally:
                async with async_session_factory() as session:
                    for item in await session.scalars(
                        select(Material).where(Material.user_id.in_(users))
                    ):
                        keys.add(item.s3_key)
                    for item in await session.scalars(
                        select(MaterialImage).where(MaterialImage.user_id.in_(users))
                    ):
                        keys.add(item.s3_key)
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
                for key in keys:
                    storage.delete(key)
