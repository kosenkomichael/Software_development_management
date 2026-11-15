"""Server-timed public training attempts."""

import sqlalchemy as sa

from alembic import op

revision = "b6e1f4a8c015"
down_revision = "a5d0e3f7b904"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("quiz_attempts", sa.Column("run_id", sa.UUID(), nullable=True))
    op.add_column("quiz_attempts", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_quiz_attempts_run_id", "quiz_attempts", ["run_id"])


def downgrade():
    op.drop_constraint("uq_quiz_attempts_run_id", "quiz_attempts", type_="unique")
    op.drop_column("quiz_attempts", "duration_ms")
    op.drop_column("quiz_attempts", "run_id")
