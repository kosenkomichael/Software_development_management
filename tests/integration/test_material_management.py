"""Local API check. Enable with RUN_LOCAL_API_TESTS=1."""

import os
import secrets
import unittest
import uuid

import httpx
from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models import Material, User


@unittest.skipUnless(os.getenv("RUN_LOCAL_API_TESTS") == "1", "Requires local API")
class MaterialManagementTests(unittest.IsolatedAsyncioTestCase):
    async def test_rename_favorite_ownership_and_removal(self):
        users, tokens, headers = [], [], []
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=20) as client:
            try:
                for _ in range(2):
                    credentials = {
                        "email": f"material-{uuid.uuid4().hex}@example.com",
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
                        original_filename="original.pdf",
                        s3_key="temporary-no-object",
                        content_type="application/pdf",
                        size_bytes=10,
                    )
                    session.add(material)
                    await session.commit()
                    mid = str(material.id)
                path = f"/materials/{mid}"
                response = await client.patch(
                    path, headers=headers[1], json={"original_filename": "foreign.pdf"}
                )
                self.assertEqual(response.status_code, 404)
                response = await client.delete(path, headers=headers[1])
                self.assertEqual(response.status_code, 404)
                for name in ["   ", "../file.pdf", "line\nbreak.pdf"]:
                    response = await client.patch(
                        path, headers=headers[0], json={"original_filename": name}
                    )
                    self.assertEqual(response.status_code, 422)
                response = await client.patch(
                    path,
                    headers=headers[0],
                    json={"original_filename": "Renamed.pdf", "is_favorite": True},
                )
                response.raise_for_status()
                self.assertEqual(response.json()["original_filename"], "Renamed.pdf")
                self.assertTrue(response.json()["is_favorite"])
                response = await client.get(path, headers=headers[0])
                response.raise_for_status()
                self.assertTrue(response.json()["is_favorite"])
                download_url = response.json()["download_url"]
                response = await client.get("/materials/", headers=headers[0])
                self.assertEqual(response.json()["items"][0]["original_filename"], "Renamed.pdf")
                response = await client.patch(path, headers=headers[0], json={"is_favorite": False})
                self.assertFalse(response.json()["is_favorite"])
                response = await client.delete(path, headers=headers[0])
                self.assertEqual(response.status_code, 204)
                for suffix in [
                    "",
                    "/notes",
                    "/notes/status",
                    "/quiz",
                    "/quiz/status",
                    "/quiz/attempts",
                    "/images/1",
                ]:
                    response = await client.get(path + suffix, headers=headers[0])
                    self.assertEqual(response.status_code, 404, suffix)
                response = await client.get("http://127.0.0.1:8000" + download_url)
                self.assertEqual(response.status_code, 404)
                response = await client.get("/materials/", headers=headers[0])
                self.assertEqual(response.json(), {"items": [], "total": 0})
                response = await client.patch(path, headers=headers[0], json={"is_favorite": True})
                self.assertEqual(response.status_code, 404)
                response = await client.get("/auth/me/stats", headers=headers[0])
                self.assertEqual(response.json()["materials_count"], 0)
                response = await client.get("/auth/me/activity", headers=headers[0])
                self.assertEqual(response.json(), {"items": [], "total": 0})
                async with async_session_factory() as session:
                    removed = await session.get(Material, uuid.UUID(mid))
                    self.assertIsNotNone(removed.deleted_at)
            finally:
                for token in tokens:
                    await client.post(
                        "/auth/logout", json={"refresh_token": token["refresh_token"]}
                    )
                async with async_session_factory() as session:
                    await session.execute(delete(User).where(User.id.in_(users)))
                    await session.commit()
