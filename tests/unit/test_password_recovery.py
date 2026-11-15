import hashlib
import json
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import BackgroundTasks, HTTPException
from pydantic import ValidationError

from app.core.security import credential_version, hash_password, verify_password
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService


class PasswordRecoveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis = AsyncMock()
        self.session = AsyncMock()
        self.service = AuthService(self.session, self.redis)
        self.user = SimpleNamespace(
            id=uuid.uuid4(),
            email="recovery@example.com",
            is_active=True,
            hashed_password=hash_password("original-password"),
        )
        self.service._repo.get_by_email = AsyncMock(return_value=self.user)
        self.service._repo.get_by_id = AsyncMock(return_value=self.user)

    async def test_unknown_email_does_not_send_mail(self):
        self.service._repo.get_by_email.return_value = None
        background = BackgroundTasks()
        with self.assertRaises(HTTPException) as error:
            await self.service.forgot_password("missing@example.com", background)
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(background.tasks, [])
        self.redis.setex.assert_not_awaited()

    async def test_link_has_expiry_and_redis_only_stores_digest(self):
        background = BackgroundTasks()
        await self.service.forgot_password(self.user.email, background)
        link = background.tasks[0].args[1]
        token = link.split("#token=")[1]
        key, ttl, data = self.redis.setex.call_args.args
        self.assertEqual(key, "password-reset:" + hashlib.sha256(token.encode()).hexdigest())
        self.assertEqual(ttl, 1800)
        self.assertNotIn(token, data)

    async def test_cooldown_does_not_send_mail(self):
        self.redis.set.return_value = False
        self.redis.ttl.return_value = 42
        background = BackgroundTasks()
        remaining = await self.service.forgot_password(self.user.email, background)
        self.assertEqual(remaining, 42)
        self.assertEqual(background.tasks, [])

    async def test_reset_changes_password_and_token_cannot_be_reused(self):
        data = json.dumps(
            {"uid": str(self.user.id), "cv": credential_version(self.user.hashed_password)}
        )
        self.redis.getdel.side_effect = [data, None]
        self.session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=self.user))
        old_version = credential_version(self.user.hashed_password)
        await self.service.reset_password("a" * 43, "replacement-password")
        self.assertTrue(verify_password("replacement-password", self.user.hashed_password))
        self.assertNotEqual(old_version, credential_version(self.user.hashed_password))
        self.session.commit.assert_awaited_once()
        with self.assertRaises(HTTPException) as error:
            await self.service.reset_password("a" * 43, "another-password")
        self.assertEqual(error.exception.status_code, 400)

    async def test_other_link_is_invalid_after_password_change(self):
        self.redis.getdel.return_value = json.dumps({"uid": str(self.user.id), "cv": "old-version"})
        self.session.execute.return_value = Mock(scalar_one_or_none=Mock(return_value=self.user))
        with self.assertRaises(HTTPException):
            await self.service.reset_password("a" * 43, "replacement-password")
        self.session.commit.assert_not_awaited()

    async def test_old_refresh_token_rejected_after_password_change(self):
        tokens = await self.service._issue_tokens(str(self.user.id))
        self.user.hashed_password = hash_password("replacement-password")
        with self.assertRaises(HTTPException) as error:
            await self.service.refresh(tokens.refresh_token)
        self.assertEqual(error.exception.status_code, 401)


class RecoveryValidationTests(unittest.TestCase):
    def test_email_normalized(self):
        self.assertEqual(
            ForgotPasswordRequest(email=" Test@Example.com ").email, "test@example.com"
        )

    def test_weak_password_rejected(self):
        with self.assertRaises(ValidationError):
            ResetPasswordRequest(token="a" * 43, password="short")
