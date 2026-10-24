import enum
import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MaterialStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    failed = "failed"


class Material(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "materials"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(nullable=False)
    s3_key: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus), default=MaterialStatus.uploaded, nullable=False
    )

    note: Mapped["Note"] = relationship("Note", back_populates="material", uselist=False)  # noqa: F821
    images: Mapped[list["MaterialImage"]] = relationship(  # noqa: F821
        "MaterialImage", back_populates="material", cascade="all, delete-orphan", order_by="MaterialImage.order"
    )
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="material")  # noqa: F821
