from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

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
    title: str | None = None
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
    run_id: UUID | None = None
    quiz_id: UUID | None = None
    answers: list[SubmitAnswerItem]


class QuestionResult(BaseModel):
    question_id: str
    is_correct: bool
    correct_ids: list[str]
    explanation: str | None = None


class SubmitResponse(BaseModel):
    duration_ms: int | None = None
    attempt_id: str | None = None
    score: float
    total: int
    correct: int
    results: list[QuestionResult]


class AttemptSummary(BaseModel):
    duration_ms: int | None = None
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


class PublicationRequest(BaseModel):
    is_public: bool
    title: str | None = Field(default=None, min_length=1, max_length=200)


class PublicationResponse(BaseModel):
    is_public: bool
    title: str


class PublicQuizSummary(BaseModel):
    id: str
    title: str
    author: str
    published_at: datetime
    question_count: int


class PublicQuizList(BaseModel):
    items: list[PublicQuizSummary]
    total: int


class PublicAttemptSummary(AttemptSummary):
    title: str


class PublicAttemptList(BaseModel):
    items: list[PublicAttemptSummary]
    total: int


class TrainingRunResponse(BaseModel):
    run_id: UUID
    started_at: datetime
    server_time: datetime


class LeaderboardEntry(BaseModel):
    rank: int
    name: str
    score: float
    correct: int
    total: int
    duration_ms: int
    is_you: bool


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardEntry]
    participants: int
    my_entry: LeaderboardEntry | None = None


class TrainingRunRequest(BaseModel):
    run_id: UUID
