import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.quiz import Quiz


class MaterialStatus(enum.StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    failed = "failed"


class Material(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "materials"
    __table_args__ = (
        Index(
            "uq_material_import_active",
            "user_id",
            "source_material_id",
            unique=True,
            postgresql_where=text("source_material_id IS NOT NULL AND deleted_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_favorite: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_public: Mapped[bool] = mapped_column(default=False, server_default="false", index=True)
    visibility: Mapped[str] = mapped_column(default="public", server_default="public")
    share_token: Mapped[str | None] = mapped_column(nullable=True)
    public_title: Mapped[str | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_quiz_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "quizzes.id", ondelete="SET NULL", use_alter=True, name="fk_material_published_quiz"
        ),
        nullable=True,
    )
    source_material_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="SET NULL", name="fk_material_source"),
        nullable=True,
    )
    source_author: Mapped[str | None] = mapped_column(nullable=True)

    original_filename: Mapped[str] = mapped_column(nullable=False)
    s3_key: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus), default=MaterialStatus.uploaded, nullable=False
    )

    note: Mapped["Note"] = relationship("Note", back_populates="material", uselist=False)  # noqa: F821
    images: Mapped[list["MaterialImage"]] = relationship(  # noqa: F821
        "MaterialImage",
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialImage.order",
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz", back_populates="material", foreign_keys="Quiz.material_id"
    )  # noqa: F821
