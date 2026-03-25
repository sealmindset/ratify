# Changelog

All notable changes to Ratify will be documented in this file.

## [0.3.0] - 2026-03-24

### Added
- Activity Logs with in-memory circular buffer (10,000 events)
- Inbound request middleware and outbound HTTP interceptors
- Admin UI Activity Logs tab with stats cards, filters, event table, auto-refresh
- admin.logs.read and admin.logs.delete RBAC permissions

## [0.2.0] - 2026-03-24

### Added
- Inline document comments with quoted text anchoring
- Threaded comment replies (parent_id)
- Resolve/unresolve comments via PATCH
- Tier 2 Prompt Management system (11 managed prompts)
- Admin UI for prompt editing with version history and test preview
- Prompt service with database-first loading, code fallback, 60s cache TTL
- Categories: Interview, Generation, Refinement, Assistance

## [0.1.0] - 2026-03-24

### Added
- Project scaffolding with FastAPI backend and Next.js frontend
- OIDC authentication with mock-oidc for local development
- Database-driven RBAC with 4 system roles (Super Admin, Admin, Manager, User)
- Admin UI for user management, role management, and application settings
- Docker Compose orchestration with health checks (5 services)
- Standard UI components (DataTable, Breadcrumbs, QuickSearch, ModeToggle)
- Dark/light theme support with oklch color system
- Same-origin proxy pattern (Next.js rewrites /api/* to backend)
- Environment-based configuration (.env.example documented)
- Domain models: RFC, sections, comments, reviews, sign-offs, references
- Domain API routes: RFC CRUD, AI interview, AI refinement, Jira sync
- Domain frontend pages: Dashboard, RFC Registry, RFC Detail, My Reviews
- Mock-jira service for local Jira integration testing
- AI provider abstraction (Anthropic Messages API, demo mode fallback)
- Seed data for all domain entities with 6 sample RFCs
- Mock-oidc test users aligned to database seed users
