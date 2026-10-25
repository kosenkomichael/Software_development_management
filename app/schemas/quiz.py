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
    open_answer: str | None = None


class SubmitRequest(BaseModel):
    answers: list[SubmitAnswerItem]


class QuestionResult(BaseModel):
    question_id: str
    is_correct: bool | None
    correct_ids: list[str]
    explanation: str | None = None


class SubmitResponse(BaseModel):
    score: float
    total: int
    correct: int
    results: list[QuestionResult]
