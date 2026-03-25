"""Domain schema -- RFCs, sections, comments, reviews, sign-offs, references, AI conversations

Revision ID: 002
Revises: 001
Create Date: 2026-03-24 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- rfcs ---
    op.create_table(
        "rfcs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_number", sa.Integer(), unique=True, nullable=False, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("rfc_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jira_epic_key", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- rfc_sections ---
    op.create_table(
        "rfc_sections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_id", UUID(as_uuid=True), sa.ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("section_type", sa.String(50), nullable=False, server_default="body"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- comments ---
    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_id", UUID(as_uuid=True), sa.ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", UUID(as_uuid=True), sa.ForeignKey("rfc_sections.id", ondelete="CASCADE"), nullable=True),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- references ---
    op.create_table(
        "references",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("comment_id", UUID(as_uuid=True), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("ref_type", sa.String(50), nullable=False, server_default="link"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- review_assignments ---
    op.create_table(
        "review_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_id", UUID(as_uuid=True), sa.ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", UUID(as_uuid=True), sa.ForeignKey("rfc_sections.id", ondelete="CASCADE"), nullable=True),
        sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("team", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jira_task_key", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- sign_offs ---
    op.create_table(
        "sign_offs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_id", UUID(as_uuid=True), sa.ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("team", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- ai_conversations ---
    op.create_table(
        "ai_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rfc_id", UUID(as_uuid=True), sa.ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rfc_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("messages_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- app_settings ---
    op.create_table(
        "app_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("group_name", sa.String(100), nullable=False, index=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("value_type", sa.String(20), nullable=False, server_default="string"),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_restart", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- app_setting_audit_logs ---
    op.create_table(
        "app_setting_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("setting_id", UUID(as_uuid=True), sa.ForeignKey("app_settings.id"), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for common queries
    op.create_index("ix_rfcs_status", "rfcs", ["status"])
    op.create_index("ix_rfcs_author_id", "rfcs", ["author_id"])
    op.create_index("ix_rfcs_rfc_type", "rfcs", ["rfc_type"])
    op.create_index("ix_rfc_sections_rfc_id", "rfc_sections", ["rfc_id"])
    op.create_index("ix_comments_rfc_id", "comments", ["rfc_id"])
    op.create_index("ix_comments_section_id", "comments", ["section_id"])
    op.create_index("ix_review_assignments_rfc_id", "review_assignments", ["rfc_id"])
    op.create_index("ix_review_assignments_reviewer_id", "review_assignments", ["reviewer_id"])
    op.create_index("ix_sign_offs_rfc_id", "sign_offs", ["rfc_id"])
    op.create_index("ix_ai_conversations_rfc_id", "ai_conversations", ["rfc_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_conversations_rfc_id")
    op.drop_index("ix_sign_offs_rfc_id")
    op.drop_index("ix_review_assignments_reviewer_id")
    op.drop_index("ix_review_assignments_rfc_id")
    op.drop_index("ix_comments_section_id")
    op.drop_index("ix_comments_rfc_id")
    op.drop_index("ix_rfc_sections_rfc_id")
    op.drop_index("ix_rfcs_rfc_type")
    op.drop_index("ix_rfcs_author_id")
    op.drop_index("ix_rfcs_status")
    op.drop_table("ai_conversations")
    op.drop_table("sign_offs")
    op.drop_table("review_assignments")
    op.drop_table("references")
    op.drop_table("comments")
    op.drop_table("rfc_sections")
    op.drop_table("rfcs")
    op.drop_table("app_setting_audit_logs")
    op.drop_table("app_settings")
