"""Profile checks against the running local API."""

import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import User


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API")
class ProfileIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_profile_email_and_password_changes(self):
        users, tokens, emails = [], [], []
        old_password = secrets.token_urlsafe(20)
        new_password = secrets.token_urlsafe(20)
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=20) as client:
            try:
                for _ in range(2):
                    email = f"profile-{uuid.uuid4().hex}@example.com"
                    emails.append(email)
                    response = await client.post(
                        "/auth/register", json={"email": email, "password": old_password}
                    )
                    response.raise_for_status()
                    users.append(uuid.UUID(response.json()["id"]))
                response = await client.post(
                    "/auth/login", json={"email": emails[0], "password": old_password}
                )
                response.raise_for_status()
                original = response.json()
                tokens.append(original)
                headers = {"Authorization": "Bearer " + original["access_token"]}
                response = await client.patch(
                    "/auth/me",
                    headers=headers,
                    json={"first_name": " Денис ", "last_name": "Тестов"},
                )
                response.raise_for_status()
                self.assertIsNone(response.json()["tokens"])
                response = await client.get("/auth/me", headers=headers)
                self.assertEqual(
                    (response.json()["first_name"], response.json()["last_name"]),
                    ("Денис", "Тестов"),
                )
                response = await client.patch(
                    "/auth/me",
                    headers=headers,
                    json={"email": emails[1], "current_password": "incorrect"},
                )
                self.assertEqual(response.status_code, 400)
                response = await client.patch(
                    "/auth/me",
                    headers=headers,
                    json={"email": emails[1], "current_password": old_password},
                )
                self.assertEqual(response.status_code, 409)
                response = await client.patch(
                    "/auth/me", headers=headers, json={"email": "bad-address"}
                )
                self.assertEqual(response.status_code, 422)
                response = await client.get("/auth/me", headers=headers)
                self.assertEqual(response.json()["email"], emails[0])
                new_email = f"changed-{uuid.uuid4().hex}@example.com"
                response = await client.patch(
                    "/auth/me",
                    headers=headers,
                    json={"email": new_email, "current_password": old_password},
                )
                response.raise_for_status()
                updated = response.json()["tokens"]
                tokens.append(updated)
                response = await client.get("/auth/me", headers=headers)
                self.assertEqual(response.status_code, 401)
                response = await client.post(
                    "/auth/refresh", json={"refresh_token": original["refresh_token"]}
                )
                self.assertEqual(response.status_code, 401)
                headers = {"Authorization": "Bearer " + updated["access_token"]}
                response = await client.get("/auth/me", headers=headers)
                self.assertEqual(response.json()["email"], new_email)
                response = await client.post(
                    "/auth/login", json={"email": emails[0], "password": old_password}
                )
                self.assertEqual(response.status_code, 401)
                response = await client.post(
                    "/auth/change-password",
                    headers=headers,
                    json={"current_password": "incorrect", "password": new_password},
                )
                self.assertEqual(response.status_code, 400)
                response = await client.post(
                    "/auth/change-password",
                    headers=headers,
                    json={"current_password": old_password, "password": "short"},
                )
                self.assertEqual(response.status_code, 422)
                response = await client.post(
                    "/auth/change-password",
                    headers=headers,
                    json={"current_password": old_password, "password": new_password},
                )
                response.raise_for_status()
                changed = response.json()
                tokens.append(changed)
                response = await client.get("/auth/me", headers=headers)
                self.assertEqual(response.status_code, 401)
                response = await client.post(
                    "/auth/refresh", json={"refresh_token": updated["refresh_token"]}
                )
                self.assertEqual(response.status_code, 401)
                response = await client.get(
                    "/auth/me", headers={"Authorization": "Bearer " + changed["access_token"]}
                )
                self.assertEqual(response.status_code, 200)
                response = await client.post(
                    "/auth/login", json={"email": new_email, "password": old_password}
                )
                self.assertEqual(response.status_code, 401)
                response = await client.post(
                    "/auth/login", json={"email": new_email, "password": new_password}
                )
                response.raise_for_status()
                tokens.append(response.json())
            finally:
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
