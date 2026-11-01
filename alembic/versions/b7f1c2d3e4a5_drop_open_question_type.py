"""drop open question type

Revision ID: b7f1c2d3e4a5
Revises: 8dcea893767a
Create Date: 2026-11-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7f1c2d3e4a5'
down_revision: Union[str, None] = '8dcea893767a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM questions WHERE question_type::text = 'open'")
    op.execute("ALTER TYPE questiontype RENAME TO questiontype_old")
    op.execute("CREATE TYPE questiontype AS ENUM ('single', 'multiple')")
    op.execute(
        "ALTER TABLE questions ALTER COLUMN question_type "
        "TYPE questiontype USING question_type::text::questiontype"
    )
    op.execute("DROP TYPE questiontype_old")


def downgrade() -> None:
    op.execute("ALTER TYPE questiontype RENAME TO questiontype_old")
    op.execute("CREATE TYPE questiontype AS ENUM ('single', 'multiple', 'open')")
    op.execute(
        "ALTER TABLE questions ALTER COLUMN question_type "
        "TYPE questiontype USING question_type::text::questiontype"
    )
    op.execute("DROP TYPE questiontype_old")
