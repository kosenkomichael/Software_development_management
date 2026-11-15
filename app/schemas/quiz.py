from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.quiz import QuestionType, QuizStatus


class AnswerResponse(BaseModel):
    id: str
    text: str
    explanation: str | None = None


class AnswerWithCorrectResponse(AnswerResponse):
    is_correct: bool


class QuestionResponse(BaseModel):
    id: str
    text: str
    question_type: QuestionType
    order: int
    answers: list[AnswerResponse]


class QuestionWithCorrectResponse(BaseModel):
    id: str
    text: str
    question_type: QuestionType
    order: int
    answers: list[AnswerWithCorrectResponse]


class QuizResponse(BaseModel):
    id: str
    material_id: str
    status: QuizStatus
    questions: list[QuestionResponse] = []


class QuizStatusResponse(BaseModel):
    material_id: str
    status: QuizStatus
    quiz_id: str | None = None


class SubmitAnswerItem(BaseModel):
    question_id: str
    selected_ids: list[str] = []


class SubmitRequest(BaseModel):
    quiz_id: UUID | None = None
    answers: list[SubmitAnswerItem]


class QuestionResult(BaseModel):
    question_id: str
    is_correct: bool
    correct_ids: list[str]
    explanation: str | None = None


class SubmitResponse(BaseModel):
    attempt_id: str | None = None
    score: float
    total: int
    correct: int
    results: list[QuestionResult]


class AttemptSummary(BaseModel):
    id: str
    quiz_id: str | None
    created_at: datetime
    score: float
    total: int
    correct: int


class AttemptListResponse(BaseModel):
    items: list[AttemptSummary]
    total: int


class AttemptDetail(AttemptSummary):
    quiz: QuizResponse
    answers: list[SubmitAnswerItem]
    result: SubmitResponse
