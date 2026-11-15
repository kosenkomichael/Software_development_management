"""Local Docker check. Set RUN_LOCAL_API_TESTS=1 and run this module with unittest."""

import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import Answer, Material, Question, Quiz, User
from app.models.quiz import QuestionType, QuizStatus


@unittest.skipUnless(
    os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires running local API and migrated database"
)
class QuizAttemptIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_persistence_validation_ownership_and_snapshot(self):
        users = []
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=20) as client:
            try:
                headers = []
                tokens = []
                for _ in range(2):
                    credentials = {
                        "email": f"history-{uuid.uuid4().hex}@example.com",
                        "password": secrets.token_urlsafe(20),
                    }
                    response = await client.post("/auth/register", json=credentials)
                    response.raise_for_status()
                    users.append(uuid.UUID(response.json()["id"]))
                    response = await client.post("/auth/login", json=credentials)
                    response.raise_for_status()
                    tokens.append(response.json())
                    headers.append({"Authorization": "Bearer " + response.json()["access_token"]})
                async with async_session_factory() as session:
                    material = Material(
                        user_id=users[0],
                        original_filename="history-test",
                        s3_key="no-object",
                        content_type="text/plain",
                        size_bytes=0,
                    )
                    session.add(material)
                    await session.flush()
                    quiz = Quiz(material_id=material.id, user_id=users[0], status=QuizStatus.done)
                    session.add(quiz)
                    await session.flush()
                    answers = []
                    for i in range(2):
                        question = Question(
                            quiz_id=quiz.id,
                            text=f"Saved question {i}",
                            question_type=QuestionType.single,
                            order=i + 1,
                        )
                        session.add(question)
                        await session.flush()
                        correct = Answer(
                            question_id=question.id,
                            text="Correct",
                            is_correct=True,
                            explanation="Saved explanation",
                        )
                        wrong = Answer(question_id=question.id, text="Wrong", is_correct=False)
                        session.add_all([correct, wrong])
                        await session.flush()
                        answers.append(
                            {"question_id": str(question.id), "selected_ids": [str(correct.id)]}
                        )
                    await session.commit()
                    mid, qid = str(material.id), str(quiz.id)
                path = f"/materials/{mid}/quiz"
                response = await client.post(
                    path + "/submit",
                    headers=headers[0],
                    json={"quiz_id": qid, "answers": answers[:1]},
                )
                self.assertEqual(response.status_code, 422)
                response = await client.post(
                    path + "/submit",
                    headers=headers[0],
                    json={"quiz_id": qid, "answers": [answers[0], answers[0]]},
                )
                self.assertEqual(response.status_code, 422)
                response = await client.get(path + "/attempts", headers=headers[0])
                self.assertEqual(response.json()["total"], 0)
                skipped = [
                    answers[0],
                    {"question_id": answers[1]["question_id"], "selected_ids": []},
                ]
                response = await client.post(
                    path + "/submit",
                    headers=headers[0],
                    json={"quiz_id": qid, "answers": skipped},
                )
                response.raise_for_status()
                self.assertEqual((response.json()["score"], response.json()["total"]), (0.5, 2))
                early_id = response.json()["attempt_id"]
                response = await client.get(path + "/attempts/" + early_id, headers=headers[0])
                response.raise_for_status()
                self.assertEqual(response.json()["answers"][1]["selected_ids"], [])
                self.assertFalse(response.json()["result"]["results"][1]["is_correct"])
                for _ in range(2):
                    response = await client.post(
                        path + "/submit",
                        headers=headers[0],
                        json={"quiz_id": qid, "answers": answers},
                    )
                    response.raise_for_status()
                    self.assertEqual(response.json()["score"], 1)
                    attempt_id = response.json()["attempt_id"]
                response = await client.get("/auth/me/stats", headers=headers[0])
                response.raise_for_status()
                self.assertEqual(response.json()["materials_count"], 1)
                self.assertEqual(response.json()["attempts_count"], 3)
                self.assertAlmostEqual(response.json()["average_score"], 2.5 / 3)
                response = await client.get("/auth/me/stats", headers=headers[1])
                self.assertEqual(
                    response.json(),
                    {"materials_count": 0, "attempts_count": 0, "average_score": None},
                )
                response = await client.get("/auth/me/activity?page_size=1", headers=headers[0])
                response.raise_for_status()
                self.assertEqual(response.json()["total"], 4)
                self.assertEqual(len(response.json()["items"]), 1)
                self.assertEqual(response.json()["items"][0]["id"], attempt_id)
                self.assertEqual(response.json()["items"][0]["kind"], "attempt")
                response = await client.get(
                    "/auth/me/activity?page=2&page_size=1", headers=headers[0]
                )
                self.assertEqual(len(response.json()["items"]), 1)
                self.assertNotEqual(response.json()["items"][0]["id"], attempt_id)
                response = await client.get("/auth/me/activity", headers=headers[1])
                self.assertEqual(response.json(), {"items": [], "total": 0})
                # A separate client models a page reload.
                async with httpx.AsyncClient(base_url=client.base_url) as reloaded:
                    response = await reloaded.get(
                        path + "/attempts?page_size=1", headers=headers[0]
                    )
                    self.assertEqual(response.json()["total"], 3)
                    self.assertEqual(len(response.json()["items"]), 1)
                    self.assertEqual(response.json()["items"][0]["id"], attempt_id)
                response = await client.get(path + "/attempts/" + attempt_id, headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.get(path + "/attempts", headers=headers[1])
                self.assertEqual(response.status_code, 404)
                # Deleting the original quiz must leave the saved snapshot readable.
                async with async_session_factory() as session:
                    await session.execute(delete(Quiz).where(Quiz.id == uuid.UUID(qid)))
                    await session.commit()
                response = await client.get(path + "/attempts/" + attempt_id, headers=headers[0])
                response.raise_for_status()
                saved = response.json()
                self.assertIsNone(saved["quiz_id"])
                self.assertEqual(saved["answers"], answers)
                self.assertEqual(saved["quiz"]["questions"][0]["text"], "Saved question 0")
                self.assertEqual(saved["result"]["results"][0]["explanation"], "Saved explanation")
                self.assertEqual(saved["result"]["correct"], 2)
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
            finally:
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
