import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pydantic import ValidationError

from app.core.jwt import create_refresh_token, decode_refresh_token
from app.services.auth_service import AuthService
from app.services.quiz_service import _QuizSchema


class RefreshTokenTests(unittest.IsolatedAsyncioTestCase):
    async def test_refresh_uses_the_identifier_stored_in_redis(self):
        redis = AsyncMock()
        stored = {}
        redis.setex.side_effect = lambda key, ttl, value: stored.update({key: value})
        redis.getdel.side_effect = lambda key: stored.pop(key, None)
        redis.delete.side_effect = lambda key: stored.pop(key, None)
        service = AuthService(AsyncMock(), redis)
        user_id = str(uuid.uuid4())
        service._repo.get_by_id = AsyncMock(
            return_value=SimpleNamespace(is_active=True, hashed_password="hash")
        )
        original = await service._issue_tokens(user_id)
        renewed = await service.refresh(original.refresh_token)
        self.assertNotEqual(original.refresh_token, renewed.refresh_token)
        payload = decode_refresh_token(renewed.refresh_token)
        self.assertEqual(stored[f"refresh:{payload['jti']}"], user_id)
        await service.logout(renewed.refresh_token)
        self.assertEqual(stored, {})

    async def test_refresh_identifier_matches_returned_identifier(self):
        token, identifier = create_refresh_token("test-user")
        self.assertEqual(decode_refresh_token(token)["jti"], identifier)


class QuizSizeTests(unittest.TestCase):
    def question(self):
        return {
            "text": "Question",
            "type": "single",
            "answers": [
                {"text": "Correct", "is_correct": True},
                {"text": "Incorrect", "is_correct": False},
            ],
        }

    def test_accepts_short_and_full_quizzes(self):
        for count in (1, 3, 10):
            with self.subTest(count=count):
                quiz = _QuizSchema.model_validate(
                    {"questions": [self.question() for _ in range(count)]}
                )
                self.assertEqual(len(quiz.questions), count)

    def test_rejects_empty_and_oversized_quizzes(self):
        for count in (0, 11):
            with self.subTest(count=count), self.assertRaises(ValidationError):
                _QuizSchema.model_validate({"questions": [self.question() for _ in range(count)]})

    def test_short_quiz_still_requires_valid_answers(self):
        question = self.question()
        question["answers"][1]["is_correct"] = True
        with self.assertRaises(ValidationError):
            _QuizSchema.model_validate({"questions": [question]})
