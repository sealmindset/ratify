"""Seed data -- roles, permissions, users, and sample RFCs

Revision ID: 003
Revises: 002
Create Date: 2026-03-24 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Deterministic UUIDs for seed data
ROLE_SUPER_ADMIN = "00000000-0000-0000-0000-000000000001"
ROLE_ADMIN = "00000000-0000-0000-0000-000000000002"
ROLE_MANAGER = "00000000-0000-0000-0000-000000000003"
ROLE_USER = "00000000-0000-0000-0000-000000000004"

USER_ADMIN = "10000000-0000-0000-0000-000000000001"
USER_MANAGER = "10000000-0000-0000-0000-000000000002"
USER_ENGINEER = "10000000-0000-0000-0000-000000000003"
USER_VIEWER = "10000000-0000-0000-0000-000000000004"

RFC_1 = "20000000-0000-0000-0000-000000000001"
RFC_2 = "20000000-0000-0000-0000-000000000002"
RFC_3 = "20000000-0000-0000-0000-000000000003"

_ra1 = "50000000-0000-0000-0000-000000000001"
_ra2 = "50000000-0000-0000-0000-000000000002"
_ra3 = "50000000-0000-0000-0000-000000000003"


def upgrade() -> None:
    # ---- Roles ----
    roles = sa.table("roles", sa.column("id"), sa.column("name"), sa.column("description"), sa.column("is_system"))
    op.execute(
        roles.insert().values([
            {"id": ROLE_SUPER_ADMIN, "name": "Super Admin", "description": "Full system control", "is_system": True},
            {"id": ROLE_ADMIN, "name": "Admin", "description": "Manages users, settings, and RFC templates", "is_system": True},
            {"id": ROLE_MANAGER, "name": "Manager", "description": "Creates RFCs, assigns reviewers, approves sign-offs", "is_system": True},
            {"id": ROLE_USER, "name": "User", "description": "Views RFCs, submits comments, completes reviews", "is_system": True},
        ])
    )

    # ---- Permissions ----
    perms = sa.table("permissions", sa.column("id"), sa.column("resource"), sa.column("action"), sa.column("description"))

    perm_rows = []
    perm_id = 1
    permission_defs = [
        # RFC management
        ("rfcs", "create", "Create new RFCs"),
        ("rfcs", "read", "View RFCs"),
        ("rfcs", "update", "Edit RFCs"),
        ("rfcs", "delete", "Delete RFCs"),
        ("rfcs.sections", "create", "Add RFC sections"),
        ("rfcs.sections", "read", "View RFC sections"),
        ("rfcs.sections", "update", "Edit RFC sections"),
        ("rfcs.sections", "delete", "Delete RFC sections"),
        # Reviews
        ("reviews", "create", "Create review assignments"),
        ("reviews", "read", "View review assignments"),
        ("reviews", "update", "Update review status"),
        ("reviews", "delete", "Delete review assignments"),
        # Comments
        ("comments", "create", "Add comments"),
        ("comments", "read", "View comments"),
        ("comments", "update", "Edit comments"),
        ("comments", "delete", "Delete comments"),
        # Sign-offs
        ("signoffs", "create", "Request sign-offs"),
        ("signoffs", "read", "View sign-offs"),
        ("signoffs", "update", "Approve/reject sign-offs"),
        ("signoffs", "delete", "Delete sign-offs"),
        # AI
        ("ai", "interview", "Start AI interviews"),
        ("ai", "refine", "Use AI to refine sections"),
        ("ai", "extract", "Extract tasks from RFCs"),
        # Jira
        ("jira", "sync", "Sync RFCs to Jira"),
        ("jira", "read", "View Jira status"),
        # Admin
        ("admin.users", "create", "Create users"),
        ("admin.users", "read", "View users"),
        ("admin.users", "update", "Edit users"),
        ("admin.users", "delete", "Delete users"),
        ("admin.roles", "create", "Create roles"),
        ("admin.roles", "read", "View roles"),
        ("admin.roles", "update", "Edit roles"),
        ("admin.roles", "delete", "Delete roles"),
        ("admin.settings", "read", "View settings"),
        ("admin.settings", "update", "Edit settings"),
        ("admin.logs", "read", "View activity logs"),
        ("admin.logs", "delete", "Clear activity logs"),
        # Compat with scaffold permission names
        ("users", "view", "View users (compat)"),
        ("users", "create", "Create users (compat)"),
        ("users", "edit", "Edit users (compat)"),
        ("users", "delete", "Delete users (compat)"),
        ("roles", "view", "View roles (compat)"),
        ("roles", "create", "Create roles (compat)"),
        ("roles", "edit", "Edit roles (compat)"),
        ("roles", "delete", "Delete roles (compat)"),
        ("settings", "view", "View settings (compat)"),
        ("settings", "edit", "Edit settings (compat)"),
    ]

    for resource, action, description in permission_defs:
        perm_uuid = f"30000000-0000-0000-0000-{perm_id:012d}"
        perm_rows.append({"id": perm_uuid, "resource": resource, "action": action, "description": description})
        perm_id += 1

    op.execute(perms.insert().values(perm_rows))

    # ---- Role-Permission mappings ----
    rp = sa.table("role_permissions", sa.column("role_id"), sa.column("permission_id"))

    # Super Admin gets ALL permissions
    super_admin_rps = [{"role_id": ROLE_SUPER_ADMIN, "permission_id": p["id"]} for p in perm_rows]
    op.execute(rp.insert().values(super_admin_rps))

    # Admin gets all except delete permissions on critical resources
    admin_rps = [
        {"role_id": ROLE_ADMIN, "permission_id": p["id"]}
        for p in perm_rows
        if not (p["resource"] in ("rfcs", "admin.roles") and p["action"] == "delete")
    ]
    op.execute(rp.insert().values(admin_rps))

    # Manager gets RFC CRUD, reviews, comments, signoffs, AI, Jira, read admin
    manager_resources = {"rfcs", "rfcs.sections", "reviews", "comments", "signoffs", "ai", "jira"}
    manager_rps = [
        {"role_id": ROLE_MANAGER, "permission_id": p["id"]}
        for p in perm_rows
        if p["resource"] in manager_resources
        or (p["resource"] in ("admin.users", "admin.roles", "admin.settings", "admin.logs", "users", "roles", "settings") and p["action"] in ("read", "view"))
    ]
    op.execute(rp.insert().values(manager_rps))

    # User gets read + create comments + read reviews
    user_rps = [
        {"role_id": ROLE_USER, "permission_id": p["id"]}
        for p in perm_rows
        if (p["resource"] in ("rfcs", "rfcs.sections", "signoffs") and p["action"] == "read")
        or (p["resource"] == "comments" and p["action"] in ("create", "read", "update"))
        or (p["resource"] == "reviews" and p["action"] in ("read", "update"))
        or (p["resource"] == "jira" and p["action"] == "read")
    ]
    op.execute(rp.insert().values(user_rps))

    # ---- Users ----
    users = sa.table("users", sa.column("id"), sa.column("oidc_subject"), sa.column("email"), sa.column("display_name"), sa.column("is_active"), sa.column("role_id"))
    op.execute(
        users.insert().values([
            {"id": USER_ADMIN, "oidc_subject": "mock-admin", "email": "admin@ratify.local", "display_name": "Admin User", "is_active": True, "role_id": ROLE_SUPER_ADMIN},
            {"id": USER_MANAGER, "oidc_subject": "mock-manager", "email": "manager@ratify.local", "display_name": "Sarah Chen", "is_active": True, "role_id": ROLE_MANAGER},
            {"id": USER_ENGINEER, "oidc_subject": "mock-user", "email": "engineer@ratify.local", "display_name": "Alex Rivera", "is_active": True, "role_id": ROLE_USER},
            {"id": USER_VIEWER, "oidc_subject": "mock-viewer", "email": "viewer@ratify.local", "display_name": "Jordan Kim", "is_active": True, "role_id": ROLE_USER},
        ])
    )

    # ---- Sample RFCs ----
    rfcs = sa.table("rfcs", sa.column("id"), sa.column("rfc_number"), sa.column("title"), sa.column("summary"), sa.column("rfc_type"), sa.column("status"), sa.column("author_id"))
    op.execute(
        rfcs.insert().values([
            {
                "id": RFC_1, "rfc_number": 1,
                "title": "Zero Trust Network Architecture for Oracle MSCA",
                "summary": "Proposes a zero-trust security model for Oracle Manufacturing Shop Calendar integration, including mTLS, JWT-based auth, and network segmentation.",
                "rfc_type": "security", "status": "in_review", "author_id": USER_MANAGER,
            },
            {
                "id": RFC_2, "rfc_number": 2,
                "title": "CI/CD Pipeline Standardization",
                "summary": "Standardize CI/CD pipelines across all teams using GitHub Actions, with shared workflows for security scanning, testing, and deployment.",
                "rfc_type": "process", "status": "approved", "author_id": USER_ADMIN,
            },
            {
                "id": RFC_3, "rfc_number": 3,
                "title": "Microservice Event Bus Architecture",
                "summary": "Design an event-driven architecture using Apache Kafka for inter-service communication, replacing direct REST calls between microservices.",
                "rfc_type": "architecture", "status": "draft", "author_id": USER_MANAGER,
            },
        ])
    )

    # ---- RFC Sections for RFC_1 ----
    sections = sa.table("rfc_sections", sa.column("id"), sa.column("rfc_id"), sa.column("title"), sa.column("content"), sa.column("section_type"), sa.column("order"))
    rfc1_sections = [
        ("40000000-0000-0000-0000-000000000001", "Purpose & Scope", "This RFC proposes implementing a zero-trust security architecture for the Oracle MSCA integration. The scope covers network segmentation, authentication flows, and data encryption requirements.", "summary", 1),
        ("40000000-0000-0000-0000-000000000002", "Background", "The current Oracle MSCA integration uses a traditional perimeter-based security model with VPN tunnels. As we move to cloud-native infrastructure, we need to adopt zero-trust principles.", "background", 2),
        ("40000000-0000-0000-0000-000000000003", "Architecture Overview", "The proposed architecture uses mutual TLS for service-to-service communication, JWT tokens for user authentication, and network policies for micro-segmentation.", "architecture", 3),
        ("40000000-0000-0000-0000-000000000004", "Security Considerations", "All data in transit encrypted with TLS 1.3. Data at rest encrypted with AES-256. Certificate rotation automated via cert-manager. Audit logging for all access.", "security", 4),
        ("40000000-0000-0000-0000-000000000005", "Implementation Plan", "Phase 1: mTLS setup (2 weeks). Phase 2: JWT integration (1 week). Phase 3: Network policies (1 week). Phase 4: Monitoring and audit (1 week).", "implementation", 5),
        ("40000000-0000-0000-0000-000000000006", "Risk Analysis", "Risk: Certificate expiry causing outage. Mitigation: Automated rotation with 30-day buffer. Risk: Performance impact of encryption. Mitigation: Hardware acceleration.", "risk", 6),
    ]
    op.execute(
        sections.insert().values([
            {"id": sid, "rfc_id": RFC_1, "title": title, "content": content, "section_type": stype, "order": order}
            for sid, title, content, stype, order in rfc1_sections
        ])
    )

    # ---- RFC Sections for RFC_2 ----
    rfc2_sections = [
        ("40000000-0000-0000-0000-000000000011", "Purpose & Scope", "Standardize CI/CD pipelines across all engineering teams to improve deployment velocity, security posture, and operational consistency.", "summary", 1),
        ("40000000-0000-0000-0000-000000000012", "Current State", "Teams currently use a mix of Jenkins, CircleCI, and GitHub Actions. No shared security scanning or deployment standards exist.", "background", 2),
        ("40000000-0000-0000-0000-000000000013", "Proposed Pipeline", "GitHub Actions with reusable workflows. Stages: lint, test, SAST scan, container build, deploy to staging, integration tests, deploy to production.", "architecture", 3),
    ]
    op.execute(
        sections.insert().values([
            {"id": sid, "rfc_id": RFC_2, "title": title, "content": content, "section_type": stype, "order": order}
            for sid, title, content, stype, order in rfc2_sections
        ])
    )

    # ---- Review Assignments (literal SQL to avoid asyncpg UUID/VARCHAR mismatch) ----
    op.execute(sa.text(
        "INSERT INTO review_assignments (id, rfc_id, reviewer_id, team, status, deadline) VALUES "
        f"('{_ra1}'::uuid, '{RFC_1}'::uuid, '{USER_ENGINEER}'::uuid, 'Security', 'pending', '2026-04-07T00:00:00+00:00'::timestamptz), "
        f"('{_ra2}'::uuid, '{RFC_1}'::uuid, '{USER_VIEWER}'::uuid, 'Infrastructure', 'pending', '2026-04-07T00:00:00+00:00'::timestamptz), "
        f"('{_ra3}'::uuid, '{RFC_2}'::uuid, '{USER_MANAGER}'::uuid, 'Engineering', 'completed', '2026-03-20T00:00:00+00:00'::timestamptz)"
    ))

    # ---- Comments ----
    comments_t = sa.table("comments", sa.column("id"), sa.column("rfc_id"), sa.column("section_id"), sa.column("author_id"), sa.column("content"))
    op.execute(
        comments_t.insert().values([
            {"id": "60000000-0000-0000-0000-000000000001", "rfc_id": RFC_1, "section_id": "40000000-0000-0000-0000-000000000004", "author_id": USER_ENGINEER, "content": "We should also consider certificate pinning for the Oracle endpoints. This adds an extra layer of security against MITM attacks."},
            {"id": "60000000-0000-0000-0000-000000000002", "rfc_id": RFC_1, "section_id": "40000000-0000-0000-0000-000000000003", "author_id": USER_VIEWER, "content": "How will this interact with our existing load balancer configuration? We need to ensure TLS termination is handled correctly."},
            {"id": "60000000-0000-0000-0000-000000000003", "rfc_id": RFC_2, "section_id": None, "author_id": USER_ENGINEER, "content": "Great proposal! One question: how do we handle secrets management across the shared workflows?"},
        ])
    )

    # ---- Sign-offs ----
    signoffs_t = sa.table("sign_offs", sa.column("id"), sa.column("rfc_id"), sa.column("signer_id"), sa.column("team"), sa.column("status"))
    op.execute(
        signoffs_t.insert().values([
            {"id": "70000000-0000-0000-0000-000000000001", "rfc_id": RFC_1, "signer_id": USER_ADMIN, "team": "Architecture", "status": "pending"},
            {"id": "70000000-0000-0000-0000-000000000002", "rfc_id": RFC_2, "signer_id": USER_ADMIN, "team": "Architecture", "status": "approved"},
            {"id": "70000000-0000-0000-0000-000000000003", "rfc_id": RFC_2, "signer_id": USER_MANAGER, "team": "Engineering", "status": "approved"},
        ])
    )

    # ---- App Settings ----
    app_settings = sa.table(
        "app_settings",
        sa.column("key"), sa.column("value"), sa.column("group_name"),
        sa.column("display_name"), sa.column("description"),
        sa.column("value_type"), sa.column("is_sensitive"), sa.column("requires_restart"),
    )
    op.execute(
        app_settings.insert().values([
            {"key": "app.name", "value": "Ratify", "group_name": "General", "display_name": "Application Name", "description": "Application display name", "value_type": "string", "is_sensitive": False, "requires_restart": False},
            {"key": "rfc.auto_number", "value": "true", "group_name": "RFC", "display_name": "Auto-Number RFCs", "description": "Automatically assign sequential RFC numbers", "value_type": "bool", "is_sensitive": False, "requires_restart": False},
            {"key": "review.default_deadline_days", "value": "14", "group_name": "Reviews", "display_name": "Default Review Deadline", "description": "Default number of days for review deadlines", "value_type": "int", "is_sensitive": False, "requires_restart": False},
            {"key": "jira.project_key", "value": "RAT", "group_name": "Jira", "display_name": "Jira Project Key", "description": "Jira project key for RFC epics", "value_type": "string", "is_sensitive": False, "requires_restart": False},
        ])
    )


def downgrade() -> None:
    # Clear all seeded data in reverse dependency order
    for table in ["app_settings", "sign_offs", "comments", "review_assignments", "rfc_sections", "rfcs", "users", "role_permissions", "permissions", "roles"]:
        op.execute(sa.text(f"DELETE FROM {table}"))
