"""Full public-quiz flow against the local Docker API."""

import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import Answer, Material, Question, Quiz, QuizStatus, User
from app.models.quiz import QuestionType


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API")
class PublicQuizTests(unittest.IsolatedAsyncioTestCase):
    async def test_publication_participation_and_private_history(self):
        users, tokens, headers = [], [], []
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=20) as client:
            try:
                for _ in range(3):
                    credentials = {
                        "email": f"public-{uuid.uuid4().hex}@example.com",
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
                        original_filename="PRIVATE LECTURE.pdf",
                        s3_key="no-object",
                        content_type="application/pdf",
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
                            text=f"Question {i}",
                            question_type=QuestionType.single,
                            order=i + 1,
                        )
                        session.add(question)
                        await session.flush()
                        correct = Answer(
                            question_id=question.id,
                            text="Correct",
                            is_correct=True,
                            explanation="Explanation",
                        )
                        wrong = Answer(question_id=question.id, text="Wrong", is_correct=False)
                        session.add_all([correct, wrong])
                        await session.flush()
                        answers.append(
                            {"question_id": str(question.id), "selected_ids": [str(correct.id)]}
                        )
                    await session.commit()
                    qid, mid = str(quiz.id), str(material.id)
                path = f"/public-quizzes/{qid}"
                response = await client.get(path, headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.patch(
                    f"/quizzes/{qid}/publication",
                    headers=headers[1],
                    json={"is_public": True, "title": "Shared quiz"},
                )
                self.assertEqual(response.status_code, 404)
                response = await client.get("/public-quizzes", headers=headers[1])
                self.assertNotIn(qid, [q["id"] for q in response.json()["items"]])
                response = await client.patch(
                    f"/quizzes/{qid}/publication",
                    headers=headers[0],
                    json={"is_public": True, "title": "Shared quiz"},
                )
                response.raise_for_status()
                response = await client.get("/public-quizzes", headers=headers[1])
                response.raise_for_status()
                published = next(q for q in response.json()["items"] if q["id"] == qid)
                self.assertEqual(
                    (published["title"], published["question_count"]), ("Shared quiz", 2)
                )
                self.assertNotIn("@", published["author"])
                response = await client.get(path, headers=headers[1])
                response.raise_for_status()
                for question in response.json()["questions"]:
                    for answer in question["answers"]:
                        self.assertNotIn("is_correct", answer)
                        self.assertIsNone(answer["explanation"])
                for suffix in ["", "/notes", "/quiz"]:
                    response = await client.get(f"/materials/{mid}" + suffix, headers=headers[1])
                    self.assertEqual(response.status_code, 404)
                response = await client.post(
                    path + "/submit", headers=headers[1], json={"answers": answers[:1]}
                )
                self.assertEqual(response.status_code, 422)
                response = await client.get("/public-quizzes/attempts", headers=headers[1])
                self.assertEqual(response.json()["total"], 0)
                skipped = [
                    answers[0],
                    {"question_id": answers[1]["question_id"], "selected_ids": []},
                ]
                response = await client.post(
                    path + "/submit", headers=headers[1], json={"answers": skipped}
                )
                response.raise_for_status()
                self.assertEqual((response.json()["score"], response.json()["total"]), (0.5, 2))
                attempt_id = response.json()["attempt_id"]
                detail = f"/public-quizzes/attempts/{attempt_id}"
                response = await client.get(detail, headers=headers[1])
                response.raise_for_status()
                self.assertEqual(response.json()["answers"], skipped)
                self.assertEqual(
                    response.json()["result"]["results"][0]["explanation"], "Explanation"
                )
                for other in [0, 2]:
                    response = await client.get(detail, headers=headers[other])
                    self.assertEqual(response.status_code, 404)
                response = await client.get(
                    f"/materials/{mid}/quiz/attempts/{attempt_id}", headers=headers[0]
                )
                self.assertEqual(response.status_code, 404)
                response = await client.get("/auth/me/stats", headers=headers[1])
                self.assertEqual(
                    (
                        response.json()["materials_count"],
                        response.json()["attempts_count"],
                        response.json()["average_score"],
                    ),
                    (0, 1, 0.5),
                )
                response = await client.get("/auth/me/activity", headers=headers[1])
                self.assertEqual(response.json()["items"][0]["id"], attempt_id)
                self.assertTrue(response.json()["items"][0]["is_public"])
                response = await client.patch(
                    f"/quizzes/{qid}/publication", headers=headers[0], json={"is_public": False}
                )
                response.raise_for_status()
                response = await client.get(path, headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.post(
                    path + "/submit", headers=headers[1], json={"answers": answers}
                )
                self.assertEqual(response.status_code, 404)
                response = await client.get(detail, headers=headers[1])
                self.assertEqual(response.status_code, 200)
                # Removing the source account must not destroy another participant's snapshot.
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id == users[0]))
                    await session.commit()
                response = await client.get(detail, headers=headers[1])
                response.raise_for_status()
                self.assertIsNone(response.json()["quiz_id"])
                self.assertEqual(response.json()["quiz"]["questions"][0]["text"], "Question 0")
                response = await client.get("/public-quizzes/attempts", headers=headers[1])
                self.assertEqual(response.json()["total"], 1)
                response = await client.get("/auth/me/stats", headers=headers[1])
                self.assertEqual(response.json()["attempts_count"], 1)
                response = await client.get("/auth/me/activity", headers=headers[1])
                self.assertEqual(response.json()["items"][0]["title"], "Shared quiz")
            finally:
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
