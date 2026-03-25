"""Add inline comment fields -- quoted_text, anchor, resolved

Revision ID: 004
Revises: 003
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("quoted_text", sa.Text(), nullable=True))
    op.add_column("comments", sa.Column("anchor_offset", sa.Integer(), nullable=True))
    op.add_column("comments", sa.Column("anchor_length", sa.Integer(), nullable=True))
    op.add_column(
        "comments",
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "comments",
        sa.Column("resolved_by", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "comments",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_comments_resolved_by_users",
        "comments",
        "users",
        ["resolved_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_comments_resolved_by_users", "comments", type_="foreignkey")
    op.drop_column("comments", "resolved_at")
    op.drop_column("comments", "resolved_by")
    op.drop_column("comments", "is_resolved")
    op.drop_column("comments", "anchor_length")
    op.drop_column("comments", "anchor_offset")
    op.drop_column("comments", "quoted_text")
