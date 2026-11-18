import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.models.quiz import QuestionType, QuizStatus
from app.schemas.quiz import SubmitAnswerItem
from app.services.quiz_grading import grade_quiz


class QuizGradingTests(unittest.TestCase):
    def setUp(self):
        self.quiz = SimpleNamespace(
            id="quiz",
            material_id="material",
            status=QuizStatus.done,
            questions=[
                SimpleNamespace(
                    id=f"q{i}",
                    text=f"Question {i}",
                    order=i,
                    question_type=QuestionType.single,
                    answers=[
                        SimpleNamespace(
                            id=f"a{i}", text="Yes", is_correct=True, explanation="Because"
                        ),
                        SimpleNamespace(id=f"b{i}", text="No", is_correct=False, explanation=None),
                    ],
                )
                for i in range(2)
            ],
        )

    def answers(self):
        return [SubmitAnswerItem(question_id=f"q{i}", selected_ids=[f"a{i}"]) for i in range(2)]

    def test_full_score_and_snapshot(self):
        result, snapshot = grade_quiz(self.quiz, self.answers())
        self.assertEqual((result.score, result.correct, result.total), (1, 2, 2))
        self.assertEqual(snapshot.questions[0].text, "Question 0")
        self.assertEqual(result.results[0].correct_ids, ["a0"])

    def test_wrong_answer_reduces_score(self):
        answers = self.answers()
        answers[0].selected_ids = ["b0"]
        result, _ = grade_quiz(self.quiz, answers)
        self.assertEqual((result.score, result.correct), (0.5, 1))

    def test_incomplete_duplicate_and_foreign_answers_rejected(self):
        full = self.answers()
        cases = [
            full[:1],
            [full[0], full[0]],
            [full[0], SubmitAnswerItem(question_id="foreign", selected_ids=["a1"])],
            [full[0], SubmitAnswerItem(question_id="q1", selected_ids=["a0"])],
            [full[0], SubmitAnswerItem(question_id="q1", selected_ids=["a1", "a1"])],
            [full[0], SubmitAnswerItem(question_id="q1", selected_ids=["a1", "b1"])],
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(HTTPException) as error:
                grade_quiz(self.quiz, case)
            self.assertEqual(error.exception.status_code, 422)

    def test_multiple_choice_requires_exact_correct_set(self):
        self.quiz.questions[0].question_type = QuestionType.multiple
        self.quiz.questions[0].answers[1].is_correct = True
        answers = self.answers()
        result, _ = grade_quiz(self.quiz, answers)
        self.assertEqual(result.score, 0.5)
        answers[0].selected_ids = ["b0", "a0"]
        result, _ = grade_quiz(self.quiz, answers)
        self.assertEqual(result.score, 1)

    def test_skipped_questions_count_as_wrong(self):
        answers = self.answers()
        answers[1].selected_ids = []
        result, _ = grade_quiz(self.quiz, answers)
        self.assertEqual((result.score, result.total, result.correct), (0.5, 2, 1))
        self.assertFalse(result.results[1].is_correct)
        answers[0].selected_ids = []
        result, _ = grade_quiz(self.quiz, answers)
        self.assertEqual((result.score, result.total, result.correct), (0, 2, 0))
