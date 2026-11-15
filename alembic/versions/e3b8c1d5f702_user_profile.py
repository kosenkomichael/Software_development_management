"""Store user profile names."""

import sqlalchemy as sa

from alembic import op

revision = "e3b8c1d5f702"
down_revision = "d2a7b9c4e601"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("first_name", sa.String(), server_default="", nullable=False))
    op.add_column("users", sa.Column("last_name", sa.String(), server_default="", nullable=False))


def downgrade():
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
