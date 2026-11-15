"""Save quiz attempts with snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c9e2f8a1b604"
down_revision = "b7f1c2d3e4a5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "material_id",
            sa.UUID(),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "quiz_id", sa.UUID(), sa.ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("score", sa.Double(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("quiz_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_quiz_attempts_user_material_created",
        "quiz_attempts",
        ["user_id", "material_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_quiz_attempts_user_material_created", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
