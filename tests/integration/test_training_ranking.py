"""Server timing, opt-in rankings, replay protection and score/time ordering."""

import json
import os
import secrets
import unittest
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import delete

from app.db.redis import redis_client
from app.db.session import async_session_factory
from app.models import Answer, Material, Question, Quiz, QuizStatus, User
from app.models.quiz import QuestionType


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API and Redis")
class TrainingRankingTests(unittest.IsolatedAsyncioTestCase):
    async def test_authoritative_timing_best_attempt_and_private_answers(self):
        users, tokens, headers = [], [], []
        qid = None
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=20) as client:
            try:
                for i in range(3):
                    credentials = {
                        "email": f"training-{uuid.uuid4().hex}@example.com",
                        "password": secrets.token_urlsafe(20),
                    }
                    response = await client.post("/auth/register", json=credentials)
                    response.raise_for_status()
                    users.append(uuid.UUID(response.json()["id"]))
                    response = await client.post("/auth/login", json=credentials)
                    response.raise_for_status()
                    tokens.append(response.json())
                    headers.append({"Authorization": "Bearer " + response.json()["access_token"]})
                    response = await client.patch(
                        "/auth/me", headers=headers[-1], json={"first_name": f"Runner {i}"}
                    )
                    response.raise_for_status()
                async with async_session_factory() as session:
                    material = Material(
                        user_id=users[0],
                        original_filename="ranking",
                        s3_key="no-object",
                        content_type="text/plain",
                        size_bytes=0,
                    )
                    session.add(material)
                    await session.flush()
                    quiz = Quiz(
                        material_id=material.id,
                        user_id=users[0],
                        status=QuizStatus.done,
                        is_public=True,
                        public_title="Ranking test",
                        published_at=datetime.now(UTC),
                    )
                    session.add(quiz)
                    await session.flush()
                    qid = str(quiz.id)
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
                            explanation="Private explanation",
                        )
                        session.add_all(
                            [
                                correct,
                                Answer(question_id=question.id, text="Wrong", is_correct=False),
                            ]
                        )
                        await session.flush()
                        answers.append(
                            {"question_id": str(question.id), "selected_ids": [str(correct.id)]}
                        )
                    await session.commit()
                path = f"/public-quizzes/{qid}"
                # Old or explicitly unranked attempts must not be exposed in rankings.
                response = await client.post(
                    path + "/submit", headers=headers[2], json={"answers": answers}
                )
                response.raise_for_status()
                self.assertIsNone(response.json()["duration_ms"])
                response = await client.get(path + "/leaderboard", headers=headers[2])
                response.raise_for_status()
                self.assertEqual(response.json()["participants"], 0)
                start = await client.post(path + "/start", headers=headers[0])
                start.raise_for_status()
                original = start.json()
                repeated = await client.post(path + "/start", headers=headers[0])
                repeated.raise_for_status()
                self.assertNotEqual(repeated.json()["run_id"], original["run_id"])
                self.assertNotEqual(repeated.json()["started_at"], original["started_at"])
                original = repeated.json()
                response = await client.post(
                    path + "/submit",
                    headers=headers[0],
                    json={"run_id": original["run_id"], "answers": answers[:1]},
                )
                self.assertEqual(response.status_code, 422)
                response = await client.post(
                    path + "/submit",
                    headers=headers[2],
                    json={"run_id": original["run_id"], "answers": answers},
                )
                self.assertEqual(response.status_code, 409)

                response = await client.post(
                    path + "/heartbeat", headers=headers[0], json={"run_id": original["run_id"]}
                )
                self.assertEqual(response.status_code, 204)
                self.assertLessEqual(await redis_client.ttl(f"training:{users[0]}:{qid}"), 120)
                response = await client.post(
                    path + "/cancel", headers=headers[2], json={"run_id": original["run_id"]}
                )
                self.assertEqual(response.status_code, 204)
                self.assertIsNotNone(await redis_client.get(f"training:{users[0]}:{qid}"))
                response = await client.post(
                    path + "/cancel", headers=headers[0], json={"run_id": original["run_id"]}
                )
                self.assertEqual(response.status_code, 204)
                response = await client.post(
                    path + "/submit",
                    headers=headers[0],
                    json={"run_id": original["run_id"], "answers": answers},
                )
                self.assertEqual(response.status_code, 409)
                response = await client.post(
                    path + "/heartbeat", headers=headers[0], json={"run_id": original["run_id"]}
                )
                self.assertEqual(response.status_code, 409)

                async def finish(index, seconds, selected):
                    response = await client.post(path + "/start", headers=headers[index])
                    response.raise_for_status()
                    run_id = response.json()["run_id"]
                    key = f"training:{users[index]}:{qid}"
                    payload = json.loads(await redis_client.get(key))
                    payload["started_at"] = (
                        datetime.now(UTC) - timedelta(seconds=seconds)
                    ).isoformat()
                    await redis_client.set(key, json.dumps(payload), ex=86400)
                    # Client-supplied duration must be ignored.
                    response = await client.post(
                        path + "/submit",
                        headers=headers[index],
                        json={"run_id": run_id, "answers": selected, "duration_ms": 0},
                    )
                    response.raise_for_status()
                    result = response.json()
                    self.assertGreaterEqual(result["duration_ms"], seconds * 1000)
                    self.assertLess(result["duration_ms"], seconds * 1000 + 5000)
                    return result, run_id

                author, _ = await finish(0, 120, answers)
                fast, run_id = await finish(1, 60, answers)
                response = await client.post(
                    path + "/submit",
                    headers=headers[1],
                    json={"run_id": run_id, "answers": answers},
                )
                response.raise_for_status()
                self.assertEqual(response.json()["attempt_id"], fast["attempt_id"])
                skipped = [
                    answers[0],
                    {"question_id": answers[1]["question_id"], "selected_ids": []},
                ]
                await finish(2, 2, skipped)
                await finish(1, 90, answers)
                await finish(1, 1, skipped)
                response = await client.get(path + "/leaderboard", headers=headers[1])
                response.raise_for_status()
                board = response.json()
                self.assertEqual(board["participants"], 3)
                self.assertEqual(
                    [item["name"] for item in board["items"]], ["Runner 1", "Runner 0", "Runner 2"]
                )
                self.assertEqual(board["my_entry"]["rank"], 1)
                self.assertEqual(board["items"][0]["duration_ms"], fast["duration_ms"])
                self.assertEqual(board["items"][2]["score"], 0.5)
                for item in board["items"]:
                    self.assertNotIn("email", item)
                    self.assertNotIn("answers", item)
                    self.assertNotIn("results", item)
                response = await client.get(
                    "/public-quizzes/attempts/" + fast["attempt_id"], headers=headers[1]
                )
                response.raise_for_status()
                self.assertEqual(response.json()["duration_ms"], fast["duration_ms"])
                self.assertEqual(response.json()["result"]["duration_ms"], fast["duration_ms"])
                response = await client.get(
                    "/public-quizzes/attempts/" + fast["attempt_id"], headers=headers[0]
                )
                self.assertEqual(response.status_code, 404)
                response = await client.get(
                    f"/public-quizzes/attempts?quiz_id={qid}", headers=headers[1]
                )
                response.raise_for_status()
                self.assertEqual(response.json()["total"], 3)
                # Expired or guessed run IDs cannot enter a ranking.
                response = await client.post(
                    path + "/submit",
                    headers=headers[1],
                    json={"run_id": str(uuid.uuid4()), "answers": answers},
                )
                self.assertEqual(response.status_code, 409)
                response = await client.get(path + "/leaderboard", headers=headers[0])
                response.raise_for_status()
                self.assertEqual(response.json()["my_entry"]["duration_ms"], author["duration_ms"])
                response = await client.patch(
                    f"/quizzes/{qid}/publication", headers=headers[0], json={"is_public": False}
                )
                response.raise_for_status()
                response = await client.get(path + "/leaderboard", headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.post(path + "/start", headers=headers[1])
                self.assertEqual(response.status_code, 404)
                response = await client.get(
                    "/public-quizzes/attempts/" + fast["attempt_id"], headers=headers[1]
                )
                self.assertEqual(response.status_code, 200)
            finally:
                if qid:
                    for uid in users:
                        await redis_client.delete(f"training:{uid}:{qid}")
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
