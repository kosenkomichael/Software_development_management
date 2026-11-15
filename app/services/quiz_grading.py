from fastapi import HTTPException

from app.models.quiz import QuestionType, Quiz
from app.schemas.quiz import (
    AnswerResponse,
    QuestionResponse,
    QuestionResult,
    QuizResponse,
    SubmitAnswerItem,
    SubmitResponse,
)


def grade_quiz(
    quiz: Quiz, submitted: list[SubmitAnswerItem]
) -> tuple[SubmitResponse, QuizResponse]:
    questions = sorted(quiz.questions, key=lambda question: question.order)
    submitted_ids = [item.question_id for item in submitted]
    if (
        not questions
        or len(submitted_ids) != len(set(submitted_ids))
        or set(submitted_ids) != {str(q.id) for q in questions}
    ):
        raise HTTPException(status_code=422, detail="Answer every question exactly once")
    by_id = {item.question_id: item.selected_ids for item in submitted}
    results = []
    snapshot = []
    for question in questions:
        selected = by_id[str(question.id)]
        allowed = {str(a.id) for a in question.answers}
        if (
            len(selected) != len(set(selected))
            or not set(selected) <= allowed
            or (question.question_type == QuestionType.single and len(selected) > 1)
        ):
            raise HTTPException(status_code=422, detail="Invalid answer selection")
        correct_ids = [str(a.id) for a in question.answers if a.is_correct]
        results.append(
            QuestionResult(
                question_id=str(question.id),
                is_correct=bool(selected) and set(selected) == set(correct_ids),
                correct_ids=correct_ids,
                explanation=next(
                    (a.explanation for a in question.answers if a.is_correct and a.explanation),
                    None,
                ),
            )
        )
        snapshot.append(
            QuestionResponse(
                id=str(question.id),
                text=question.text,
                question_type=question.question_type,
                order=question.order,
                answers=[AnswerResponse(id=str(a.id), text=a.text) for a in question.answers],
            )
        )
    correct = sum(item.is_correct for item in results)
    return (
        SubmitResponse(
            score=round(correct / len(questions), 2),
            total=len(questions),
            correct=correct,
            results=results,
        ),
        QuizResponse(
            id=str(quiz.id),
            material_id=str(quiz.material_id),
            status=quiz.status,
            questions=snapshot,
        ),
    )
