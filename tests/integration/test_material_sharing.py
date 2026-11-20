"""Audience permissions through real authenticated HTTP requests."""

import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import (
    Answer,
    Material,
    MaterialStatus,
    Note,
    Question,
    QuestionType,
    Quiz,
    QuizStatus,
    User,
)


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API and database")
class MaterialSharingTests(unittest.IsolatedAsyncioTestCase):
    async def test_audiences_and_revocation(self):
        users, headers, emails = [], [], []
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=30) as client:
            try:
                for _ in range(3):
                    email = f"sharing-{uuid.uuid4().hex}@example.com"
                    body = {"email": email, "password": secrets.token_urlsafe(24)}
                    r = await client.post("/auth/register", json=body)
                    r.raise_for_status()
                    users.append(uuid.UUID(r.json()["id"]))
                    emails.append(email)
                    r = await client.post("/auth/login", json=body)
                    r.raise_for_status()
                    headers.append({"Authorization": "Bearer " + r.json()["access_token"]})
                async with async_session_factory() as db:
                    m = Material(
                        user_id=users[0],
                        original_filename="Shared.pdf",
                        s3_key="unused-sharing-fixture",
                        content_type="application/pdf",
                        size_bytes=1,
                        status=MaterialStatus.done,
                    )
                    db.add(m)
                    await db.flush()
                    db.add(
                        Note(
                            user_id=users[0],
                            material_id=m.id,
                            content="Shared note",
                            llm_model="fixture",
                            generation_time_ms=0,
                        )
                    )
                    q = Quiz(
                        user_id=users[0],
                        material_id=m.id,
                        status=QuizStatus.done,
                    )
                    db.add(q)
                    await db.flush()
                    question = Question(
                        quiz_id=q.id, text="Question", question_type=QuestionType.single, order=1
                    )
                    db.add(question)
                    await db.flush()
                    answer = Answer(question_id=question.id, text="Answer", is_correct=True)
                    db.add(answer)
                    await db.flush()
                    mid, qid, question_id, answer_id = map(
                        str, (m.id, q.id, question.id, answer.id)
                    )
                    await db.commit()
                pub = f"/materials/{mid}/publication"
                detail = f"/public-materials/{mid}"
                quiz = f"/public-quizzes/{qid}"

                async def request(method, path, actor, **kwargs):
                    return await client.request(method, path, headers=headers[actor], **kwargs)

                async def assert_blocked(actor):
                    for path in (
                        detail,
                        detail + "/download",
                        detail + "/images/1",
                        quiz,
                        quiz + "/leaderboard",
                    ):
                        r = await request("GET", path, actor)
                        self.assertEqual(r.status_code, 404, (path, r.text))
                    for path, body in (
                        (detail + "/import", {}),
                        (quiz + "/start", {}),
                        (quiz + "/submit", {"answers": []}),
                    ):
                        r = await request("POST", path, actor, json=body)
                        self.assertEqual(r.status_code, 404, (path, r.text))
                    for path in ("/public-materials?page_size=50", "/public-quizzes?page_size=50"):
                        r = await request("GET", path, actor)
                        r.raise_for_status()
                        self.assertNotIn(
                            mid if "materials" in path else qid,
                            [i["id"] for i in r.json()["items"]],
                        )

                r = await request(
                    "POST",
                    "/sharing-groups",
                    0,
                    json={"name": "Class", "emails": [emails[1].upper(), emails[1]]},
                )
                self.assertEqual(r.status_code, 201, r.text)
                gid = r.json()["id"]
                self.assertEqual(r.json()["emails"], [emails[1]])
                for method, data in [("PUT", {"name": "hijack", "emails": []}), ("DELETE", None)]:
                    r = await request(
                        method, "/sharing-groups/" + gid, 2, **({"json": data} if data else {})
                    )
                    self.assertEqual(r.status_code, 404)
                self.assertEqual((await request("GET", "/sharing-groups", 2)).json(), [])
                r = await request(
                    "PATCH",
                    pub,
                    0,
                    json={
                        "is_public": True,
                        "visibility": "groups",
                        "group_ids": [str(uuid.uuid4())],
                    },
                )
                self.assertEqual(r.status_code, 404)
                r = await request(
                    "PATCH",
                    pub,
                    0,
                    json={"is_public": True, "visibility": "groups", "group_ids": [gid]},
                )
                self.assertEqual(r.status_code, 200, r.text)
                for actor in (0, 1):
                    for path in (detail, quiz, quiz + "/leaderboard"):
                        r = await request("GET", path, actor)
                        self.assertEqual(r.status_code, 200, r.text)
                await assert_blocked(2)
                # Legacy quiz publication must obey the material audience.
                r = await request(
                    "PATCH", f"/quizzes/{qid}/publication", 0, json={"is_public": True}
                )
                self.assertEqual(r.status_code, 200, r.text)
                await assert_blocked(2)
                r = await request(
                    "PUT", "/sharing-groups/" + gid, 0, json={"name": "Class", "emails": []}
                )
                self.assertEqual(r.status_code, 200, r.text)
                await assert_blocked(1)
                r = await request("PATCH", pub, 0, json={"is_public": True, "visibility": "link"})
                self.assertEqual(r.status_code, 200, r.text)
                token = r.json()["share_token"]
                self.assertGreaterEqual(len(token), 40)
                await assert_blocked(1)
                r = await client.get(detail, headers={**headers[1], "X-Material-Share": "wrong"})
                self.assertEqual(r.status_code, 404)
                r = await client.get(detail, headers={**headers[1], "X-Material-Share": token})
                self.assertEqual(r.status_code, 200, r.text)
                self.assertNotIn("share_token", r.json())
                self.assertEqual((await request("GET", quiz, 1)).status_code, 200)
                await assert_blocked(2)
                # A completed result remains private history after access is revoked.
                r = await request("POST", quiz + "/start", 1)
                self.assertEqual(r.status_code, 200, r.text)
                run_id = r.json()["run_id"]
                r = await request(
                    "POST",
                    quiz + "/submit",
                    1,
                    json={
                        "run_id": run_id,
                        "answers": [
                            {"question_id": question_id, "selected_ids": [answer_id]}
                        ],
                    },
                )
                self.assertEqual(r.status_code, 200, r.text)
                attempt_id = r.json()["attempt_id"]
                r = await request(
                    "PATCH",
                    pub,
                    0,
                    json={"is_public": True, "visibility": "link", "rotate_link": True},
                )
                self.assertEqual(r.status_code, 200, r.text)
                new_token = r.json()["share_token"]
                self.assertNotEqual(token, new_token)
                await assert_blocked(1)
                self.assertEqual(
                    (
                        await client.get(detail, headers={**headers[1], "X-Material-Share": token})
                    ).status_code,
                    404,
                )
                self.assertEqual(
                    (await request("GET", "/public-quizzes/attempts/" + attempt_id, 1)).status_code,
                    200,
                )
                self.assertEqual(
                    (await request("GET", "/public-quizzes/attempts/" + attempt_id, 2)).status_code,
                    404,
                )
                self.assertEqual(
                    (
                        await client.get(
                            detail, headers={**headers[1], "X-Material-Share": new_token}
                        )
                    ).status_code,
                    200,
                )
                r = await request("PATCH", pub, 0, json={"is_public": False})
                self.assertEqual(r.status_code, 200, r.text)
                await assert_blocked(1)
                r = await request("PATCH", pub, 0, json={"is_public": True, "visibility": "public"})
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual((await request("GET", detail, 2)).status_code, 200)
                self.assertEqual((await request("GET", quiz, 2)).status_code, 200)
                r = await request(
                    "PATCH",
                    pub,
                    0,
                    json={"is_public": True, "visibility": "groups", "group_ids": [gid]},
                )
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(
                    (await request("DELETE", "/sharing-groups/" + gid, 0)).status_code, 204
                )
                await assert_blocked(1)
            finally:
                async with async_session_factory() as db:
                    await db.execute(delete(User).where(User.id.in_(users)))
                    await db.commit()
