import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuizStatus(str, enum.Enum):
    processing = "processing"
    done = "done"
    failed = "failed"


class QuestionType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    open = "open"


class Quiz(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quizzes"

    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[QuizStatus] = mapped_column(
        Enum(QuizStatus), default=QuizStatus.processing, nullable=False
    )

    material: Mapped["Material"] = relationship("Material", back_populates="quizzes")  # noqa: F821
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")


class Question(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    order: Mapped[int] = mapped_column(nullable=False)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped[Question] = relationship("Question", back_populates="answers")
