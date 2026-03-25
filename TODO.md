# TODO

## Planned
- [ ] Rich text editor for RFC section editing
- [ ] AI comment response assistance
- [ ] Jira Epic/sub-task auto-creation
- [ ] Sign-off tracking per team and executive approval
- [ ] RFC versioning and diff view
- [ ] Export RFC to Markdown/PDF
- [ ] Email/Slack notifications for review assignments
- [ ] Dashboard metrics and charts
- [ ] Terraform infrastructure for cloud deployment

## Completed
- [x] Full Settings admin page (grouped, masked sensitive values, audit log, RBAC)
- [x] AI provider dual-mode support (Azure AI Foundry + direct Anthropic)
- [x] Project scaffolding (FastAPI + Next.js)
- [x] OIDC authentication with mock-oidc
- [x] Database-driven RBAC (roles, permissions, role_permissions, users)
- [x] Admin UI (users, roles, settings, AI prompts, activity logs)
- [x] Docker Compose with health checks (5 services)
- [x] Standard UI components (DataTable, Breadcrumbs, QuickSearch, ModeToggle)
- [x] Environment configuration
- [x] Domain models and database migrations (RFC, sections, comments, reviews, sign-offs, references)
- [x] Domain API routes (RFC CRUD, AI interview, AI refinement, Jira sync)
- [x] Domain frontend pages (Dashboard, RFC Registry, RFC Detail, My Reviews)
- [x] Mock-jira service and AI provider abstraction
- [x] Activity logs (in-memory observability)
- [x] Seed data for all domain entities
- [x] Navigation wiring (sidebar, breadcrumbs, quick-search)
- [x] Inline document comments (create, reply, resolve, threaded)
- [x] Tier 2 Prompt Management (11 prompts, admin UI, version history, test preview)
- [x] Adaptive AI interview engine (topic tracking, follow-up probes, progress UI)
- [x] Automated tests (pytest backend 56 tests, Playwright e2e scaffolded)
