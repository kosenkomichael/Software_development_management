"""Publish and import complete study materials. Existing tests do not expose files automatically."""

import sqlalchemy as sa

from alembic import op

revision = "a5d0e3f7b904"
down_revision = "f4c9d2e6a803"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "materials", sa.Column("is_public", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column("materials", sa.Column("public_title", sa.String(), nullable=True))
    op.add_column("materials", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("materials", sa.Column("published_quiz_id", sa.UUID(), nullable=True))
    op.add_column("materials", sa.Column("source_material_id", sa.UUID(), nullable=True))
    op.add_column("materials", sa.Column("source_author", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_material_published_quiz",
        "materials",
        "quizzes",
        ["published_quiz_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_material_source",
        "materials",
        "materials",
        ["source_material_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_materials_is_public", "materials", ["is_public"])
    op.create_index(
        "uq_material_import_active",
        "materials",
        ["user_id", "source_material_id"],
        unique=True,
        postgresql_where=sa.text("source_material_id IS NOT NULL AND deleted_at IS NULL"),
    )


def downgrade():
    op.drop_index("uq_material_import_active", table_name="materials")
    op.drop_index("ix_materials_is_public", table_name="materials")
    op.drop_constraint("fk_material_source", "materials", type_="foreignkey")
    op.drop_constraint("fk_material_published_quiz", "materials", type_="foreignkey")
    for name in (
        "source_author",
        "source_material_id",
        "published_quiz_id",
        "published_at",
        "public_title",
        "is_public",
    ):
        op.drop_column("materials", name)
