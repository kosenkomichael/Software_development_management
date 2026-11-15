"""Publish quizzes and retain participants' history."""

import sqlalchemy as sa

from alembic import op

revision = "f4c9d2e6a803"
down_revision = "e3b8c1d5f702"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "quizzes", sa.Column("is_public", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column("quizzes", sa.Column("public_title", sa.String(), nullable=True))
    op.add_column("quizzes", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_quizzes_is_public", "quizzes", ["is_public"])
    op.add_column(
        "quiz_attempts",
        sa.Column("is_public_attempt", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_quiz_attempts_is_public_attempt", "quiz_attempts", ["is_public_attempt"])
    op.alter_column("quiz_attempts", "material_id", nullable=True)
    op.drop_constraint("quiz_attempts_material_id_fkey", "quiz_attempts", type_="foreignkey")
    op.create_foreign_key(
        "quiz_attempts_material_id_fkey",
        "quiz_attempts",
        "materials",
        ["material_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    # Attempts whose source has gone cannot satisfy the old NOT NULL constraint.
    op.execute("DELETE FROM quiz_attempts WHERE material_id IS NULL")
    op.drop_constraint("quiz_attempts_material_id_fkey", "quiz_attempts", type_="foreignkey")
    op.create_foreign_key(
        "quiz_attempts_material_id_fkey",
        "quiz_attempts",
        "materials",
        ["material_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("quiz_attempts", "material_id", nullable=False)
    op.drop_index("ix_quiz_attempts_is_public_attempt", table_name="quiz_attempts")
    op.drop_column("quiz_attempts", "is_public_attempt")
    op.drop_index("ix_quizzes_is_public", table_name="quizzes")
    for name in ("published_at", "public_title", "is_public"):
        op.drop_column("quizzes", name)
