"""Material favorites and removal from library."""

import sqlalchemy as sa

from alembic import op

revision = "d2a7b9c4e601"
down_revision = "c9e2f8a1b604"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "materials",
        sa.Column("is_favorite", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("materials", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("materials", "deleted_at")
    op.drop_column("materials", "is_favorite")
