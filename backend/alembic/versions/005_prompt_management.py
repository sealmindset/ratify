"""Add prompt management tables, seed prompts, and RBAC permissions

Revision ID: 005
Revises: 004
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

# Static UUIDs for seeded prompts
PROMPT_IDS = {
    "rfc-interview-infrastructure": "50000000-0000-0000-0000-000000000001",
    "rfc-interview-security":       "50000000-0000-0000-0000-000000000002",
    "rfc-interview-process":        "50000000-0000-0000-0000-000000000003",
    "rfc-interview-architecture":   "50000000-0000-0000-0000-000000000004",
    "rfc-interview-integration":    "50000000-0000-0000-0000-000000000005",
    "rfc-interview-data":           "50000000-0000-0000-0000-000000000006",
    "rfc-interview-other":          "50000000-0000-0000-0000-000000000007",
    "rfc-section-generation":       "50000000-0000-0000-0000-000000000008",
    "rfc-section-refinement":       "50000000-0000-0000-0000-000000000009",
    "rfc-comment-assistance":       "50000000-0000-0000-0000-000000000010",
    "rfc-interview-suffix":         "50000000-0000-0000-0000-000000000011",
}

# Prompt content -- extracted from ai_service.py
PROMPTS = [
    {
        "slug": "rfc-interview-infrastructure",
        "name": "RFC Interview: Infrastructure",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are an expert infrastructure architect conducting an RFC interview. "
            "Focus on: network topology, compute sizing, storage, DR/failover, security zones, "
            "monitoring, SLAs, capacity planning, and migration strategy. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-security",
        "name": "RFC Interview: Security",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are a security architect conducting an RFC interview. "
            "Focus on: threat model, authentication/authorization flows, data classification, "
            "encryption at rest and in transit, compliance requirements, audit logging, "
            "incident response, and vulnerability management. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-process",
        "name": "RFC Interview: Process",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are a process improvement specialist conducting an RFC interview. "
            "Focus on: current pain points, stakeholders, RACI matrix, success metrics, "
            "rollout plan, training needs, rollback plan, and communication strategy. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-architecture",
        "name": "RFC Interview: Architecture",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are a software architect conducting an RFC interview. "
            "Focus on: system boundaries, API contracts, data model, integration points, "
            "scalability, performance requirements, technology choices, and trade-offs. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-integration",
        "name": "RFC Interview: Integration",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are an integration specialist conducting an RFC interview. "
            "Focus on: source/target systems, data formats, transformation rules, "
            "error handling, retry policies, monitoring, SLAs, and rollback procedures. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-data",
        "name": "RFC Interview: Data",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are a data architect conducting an RFC interview. "
            "Focus on: data sources, schema design, ETL/ELT pipelines, data quality, "
            "governance, retention policies, access controls, and analytics requirements. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-other",
        "name": "RFC Interview: General",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "You are a technical architect conducting an RFC interview. "
            "Ask questions to understand the proposal thoroughly: problem statement, "
            "proposed solution, alternatives considered, risks, timeline, and success criteria. "
            "Ask one question at a time. Adapt based on answers."
        ),
    },
    {
        "slug": "rfc-interview-suffix",
        "name": "RFC Interview: Completion Suffix",
        "category": "interview",
        "model_key": "standard",
        "content": (
            "\n\nYou are interviewing someone to gather information for an RFC document. "
            "Ask focused, specific questions one at a time. When you have enough information "
            "to generate a comprehensive RFC (typically 8-15 questions), respond with exactly: "
            "INTERVIEW_COMPLETE followed by a brief summary of what you've learned."
        ),
    },
    {
        "slug": "rfc-section-generation",
        "name": "RFC Section Generation",
        "category": "generation",
        "model_key": "heavy",
        "content": (
            "Based on the interview conversation below, generate a comprehensive RFC document. "
            "Return a JSON array of sections, each with 'title', 'content' (in markdown), "
            "'section_type' (one of: summary, background, architecture, security, implementation, "
            "risk, timeline, appendix, body), and 'order' (integer starting from 1). "
            "Include these sections at minimum: Purpose & Scope, Background, Architecture Overview, "
            "Security Considerations, Implementation Plan, Risk Analysis, Open Questions, "
            "and Approval & Sign-Off. Adapt sections based on the RFC type. "
            "Return ONLY valid JSON, no other text."
        ),
    },
    {
        "slug": "rfc-section-refinement",
        "name": "RFC Section Refinement",
        "category": "refinement",
        "model_key": "standard",
        "content": "You are a technical writing assistant helping refine RFC documents.",
    },
    {
        "slug": "rfc-comment-assistance",
        "name": "RFC Comment Assistance",
        "category": "assistance",
        "model_key": "light",
        "content": "You are helping an RFC author respond to reviewer feedback constructively.",
    },
]


def upgrade() -> None:
    # ---- Tables ----
    op.create_table(
        "managed_prompts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("model_key", sa.String(50), nullable=False, server_default="standard"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "managed_prompt_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("prompt_id", UUID(as_uuid=True), sa.ForeignKey("managed_prompts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("change_summary", sa.String(500), nullable=False, server_default="Initial version"),
        sa.Column("changed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_managed_prompt_versions_prompt_id", "managed_prompt_versions", ["prompt_id"])

    # ---- Seed prompts ----
    prompts_table = sa.table(
        "managed_prompts",
        sa.column("id"), sa.column("slug"), sa.column("name"),
        sa.column("content"), sa.column("category"), sa.column("model_key"),
        sa.column("version"), sa.column("is_active"),
    )
    versions_table = sa.table(
        "managed_prompt_versions",
        sa.column("id"), sa.column("prompt_id"), sa.column("content"),
        sa.column("version"), sa.column("change_summary"),
    )

    prompt_rows = []
    version_rows = []
    for p in PROMPTS:
        pid = PROMPT_IDS[p["slug"]]
        prompt_rows.append({
            "id": pid,
            "slug": p["slug"],
            "name": p["name"],
            "content": p["content"],
            "category": p["category"],
            "model_key": p["model_key"],
            "version": 1,
            "is_active": True,
        })
        vid = f"51000000-0000-0000-0000-{len(version_rows) + 1:012d}"
        version_rows.append({
            "id": vid,
            "prompt_id": pid,
            "content": p["content"],
            "version": 1,
            "change_summary": "Initial version (seeded from code)",
        })

    op.execute(prompts_table.insert().values(prompt_rows))
    op.execute(versions_table.insert().values(version_rows))

    # ---- RBAC permissions for prompts ----
    perms = sa.table("permissions", sa.column("id"), sa.column("resource"), sa.column("action"), sa.column("description"))
    PERM_READ = "30000000-0000-0000-0000-000000000100"
    PERM_EDIT = "30000000-0000-0000-0000-000000000101"
    op.execute(perms.insert().values([
        {"id": PERM_READ, "resource": "admin.prompts", "action": "read", "description": "View managed prompts"},
        {"id": PERM_EDIT, "resource": "admin.prompts", "action": "update", "description": "Edit managed prompts"},
    ]))

    # Grant to Super Admin and Admin
    rp = sa.table("role_permissions", sa.column("role_id"), sa.column("permission_id"))
    ROLE_SUPER_ADMIN = "00000000-0000-0000-0000-000000000001"
    ROLE_ADMIN = "00000000-0000-0000-0000-000000000002"
    op.execute(rp.insert().values([
        {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_READ},
        {"role_id": ROLE_SUPER_ADMIN, "permission_id": PERM_EDIT},
        {"role_id": ROLE_ADMIN, "permission_id": PERM_READ},
        {"role_id": ROLE_ADMIN, "permission_id": PERM_EDIT},
    ]))


def downgrade() -> None:
    # Remove RBAC permissions
    rp = sa.table("role_permissions", sa.column("permission_id"))
    op.execute(rp.delete().where(rp.c.permission_id.in_([
        "30000000-0000-0000-0000-000000000100",
        "30000000-0000-0000-0000-000000000101",
    ])))
    perms = sa.table("permissions", sa.column("id"))
    op.execute(perms.delete().where(perms.c.id.in_([
        "30000000-0000-0000-0000-000000000100",
        "30000000-0000-0000-0000-000000000101",
    ])))

    op.drop_index("ix_managed_prompt_versions_prompt_id", "managed_prompt_versions")
    op.drop_table("managed_prompt_versions")
    op.drop_table("managed_prompts")
