"""Material audiences, reusable groups and revocable link access."""

import sqlalchemy as sa

from alembic import op

revision = "c7f2a5b9d126"
down_revision = "b6e1f4a8c015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "materials", sa.Column("visibility", sa.String(), nullable=False, server_default="public")
    )
    op.add_column("materials", sa.Column("share_token", sa.String(), nullable=True))
    op.create_table(
        "sharing_groups",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "owner_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
    )
    op.create_index("ix_sharing_groups_owner_id", "sharing_groups", ["owner_id"])
    op.create_table(
        "sharing_group_members",
        sa.Column(
            "group_id",
            sa.UUID(),
            sa.ForeignKey("sharing_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("email", sa.String(320), primary_key=True),
    )
    op.create_table(
        "material_groups",
        sa.Column(
            "material_id",
            sa.UUID(),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "group_id",
            sa.UUID(),
            sa.ForeignKey("sharing_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "material_link_access",
        sa.Column(
            "material_id",
            sa.UUID(),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("token", sa.String(64), nullable=False),
    )


def downgrade():
    for table in (
        "material_link_access",
        "material_groups",
        "sharing_group_members",
        "sharing_groups",
    ):
        op.drop_table(table)
    op.drop_column("materials", "share_token")
    op.drop_column("materials", "visibility")
