# Ratify

An AI-powered RFC (Request for Comments) management platform for teams that need structured technical decision-making. Ratify streamlines the entire RFC lifecycle -- from AI-guided authoring through collaborative review to formal sign-off.

## What It Does

- **AI-Driven RFC Creation** -- An adaptive interview engine asks targeted questions based on RFC type, then generates structured document sections automatically
- **Collaborative Review** -- Inline document comments with threaded replies, resolve/unresolve workflow, and AI-assisted response drafting
- **Role-Based Access Control** -- Four system roles (Super Admin, Admin, Manager, User) with granular, database-driven permissions
- **RFC Registry** -- Central dashboard for tracking all RFCs with status, ownership, and review progress
- **Sign-Off Tracking** -- Formal approval workflows for team and executive sign-off
- **Jira Integration** -- Sync RFCs with Jira for project tracking (mock service included for local dev)
- **Admin Console** -- Manage users, roles, application settings, AI prompts, and activity logs
- **Prompt Management** -- 11 managed AI prompts editable through the admin UI with version history and test preview

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python), SQLAlchemy (async), Alembic migrations |
| Database | PostgreSQL 16 |
| Auth | OIDC (mock provider for local dev, pluggable for Azure AD / Entra ID) |
| AI | Anthropic Claude (via Azure AI Foundry or direct API) |
| Infrastructure | Docker Compose (5 services) |

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- Git

That's it. Everything runs in containers.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sealmindset/ratify.git
cd ratify

# Copy the environment file
cp .env.example .env

# Generate a JWT secret
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env

# Start all services
docker compose --profile dev up --build
```

Once healthy, open **http://localhost:3100** in your browser.

### Test Users (Local Dev)

The mock OIDC provider comes pre-seeded with these accounts:

| Role | Email | Permissions |
|------|-------|-------------|
| Super Admin | admin@ratify.local | Full access (48 permissions) |
| Admin | admin2@ratify.local | Administrative access (46 permissions) |
| Manager | manager@ratify.local | RFC and review management (32 permissions) |
| User | engineer@ratify.local | Basic RFC authoring and commenting (9 permissions) |

Click "Sign In" and select a user from the login page.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Frontend        │     │  Backend          │     │  PostgreSQL  │
│  Next.js :3100   │────>│  FastAPI :8000    │────>│  :5500       │
│                  │     │                   │     │              │
│  Proxy /api/*    │     │  JWT Auth         │     │  RBAC tables │
│  Tailwind CSS    │     │  Alembic migrate  │     │  Domain data │
│  React Table     │     │  AI service       │     │              │
└─────────────────┘     └──────────────────┘     └─────────────┘
                              │          │
                    ┌─────────┘          └──────────┐
                    ▼                               ▼
            ┌──────────────┐              ┌──────────────┐
            │  mock-oidc    │              │  mock-jira    │
            │  :10090       │              │  :8543        │
            └──────────────┘              └──────────────┘
```

- **Frontend** proxies all `/api/*` requests to the backend via Next.js rewrites
- **Backend** handles auth, RBAC, CRUD, and AI orchestration
- **mock-oidc** provides a local OIDC identity provider (replaceable with Azure AD / Entra ID in production)
- **mock-jira** simulates Jira REST API for local development

### Authentication Flow

1. User clicks "Sign In" on the frontend
2. Browser redirects to the OIDC provider's authorize endpoint
3. After login, the provider redirects back with an authorization code
4. Backend exchanges the code for tokens server-to-server
5. Backend looks up the user in the database by OIDC subject, loads their role and permissions
6. A JWT is issued as an httpOnly cookie
7. All subsequent API calls include the cookie automatically

### RBAC Model

Permissions are enforced at every API endpoint using `require_permission(resource, action)` middleware. The system never checks role names directly -- only granular permissions like `rfcs.create`, `admin.settings.update`, or `reviews.read`.

## API Endpoints

| Group | Endpoints |
|-------|-----------|
| Auth | `GET /auth/login`, `GET /auth/callback`, `GET /auth/me`, `POST /auth/logout` |
| RFCs | `GET /rfcs`, `POST /rfcs`, `GET /rfcs/{id}`, `PUT /rfcs/{id}`, `DELETE /rfcs/{id}` |
| Sections | `GET /rfcs/{id}/sections`, `POST /rfcs/{id}/sections`, `PUT /sections/{id}`, `DELETE /sections/{id}` |
| Comments | `GET /rfcs/{id}/comments`, `POST /rfcs/{id}/comments`, `PATCH /comments/{id}` |
| Reviews | `GET /rfcs/{id}/reviews`, `POST /rfcs/{id}/reviews`, `GET /my-reviews` |
| Sign-Offs | `GET /rfcs/{id}/sign-offs`, `POST /rfcs/{id}/sign-offs` |
| AI | `POST /ai/interview`, `POST /ai/refine`, `POST /ai/assist` |
| Jira | `POST /jira/sync`, `GET /jira/status` |
| Admin | `GET/PUT /admin/settings`, `GET /admin/logs/events`, `GET /admin/logs/stats`, `DELETE /admin/logs/clear` |
| Users | `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}` |
| Roles | `GET /roles`, `GET /permissions` |

## AI Features

Ratify integrates with Anthropic Claude models for three capabilities:

1. **Interview Engine** -- Conducts an adaptive, topic-aware interview to gather RFC content. Tracks coverage across 8 topics per RFC type, probes for detail when answers are vague, and skips topics already covered.

2. **Section Refinement** -- Takes an existing RFC section and rewrites it based on user instructions (e.g., "make it more concise", "add risk analysis").

3. **Comment Assistance** -- Helps RFC authors draft thoughtful responses to reviewer comments.

### AI Provider Configuration

Ratify supports two AI providers. Without credentials, it runs in **demo mode** with mock responses.

**Azure AI Foundry:**
```env
AI_PROVIDER=anthropic_foundry
AZURE_AI_FOUNDRY_ENDPOINT=https://your-endpoint.azure.com
AZURE_AI_FOUNDRY_API_KEY=your-key
```

**Direct Anthropic API:**
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
```

### AI Models

| Tier | Default Model | Used For |
|------|--------------|----------|
| Heavy | claude-opus-4-6 | RFC section generation |
| Standard | claude-sonnet-4-6 | Interview conversations, refinement |
| Light | claude-haiku-4-5 | Comment assistance |

Models are configurable via `AI_MODEL_HEAVY`, `AI_MODEL_STANDARD`, and `AI_MODEL_LIGHT` environment variables.

## Configuration

All configuration is done through environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://ratify:ratify@db:5432/ratify` |
| `OIDC_ISSUER_URL` | OIDC provider URL | `http://mock-oidc:10090` |
| `OIDC_CLIENT_ID` | OIDC client ID | `mock-oidc-client` |
| `OIDC_CLIENT_SECRET` | OIDC client secret | `mock-oidc-secret` |
| `JWT_SECRET` | Secret for signing JWTs | (must be set) |
| `FRONTEND_URL` | Frontend base URL | `http://localhost:3100` |
| `BACKEND_URL` | Backend base URL | `http://localhost:8000` |
| `AI_PROVIDER` | AI backend (`anthropic_foundry` or `anthropic`) | `anthropic_foundry` |
| `JIRA_BASE_URL` | Jira instance URL | `http://mock-jira:8543` |
| `AI_RATE_LIMIT_REQUESTS_PER_MINUTE` | AI request rate limit | `20` |
| `AI_RATE_LIMIT_TOKENS_PER_MINUTE` | AI token rate limit | `50000` |
| `AI_MAX_PROMPT_CHARS` | Max prompt input size | `100000` |
| `ENFORCE_SECRETS` | Require strong secrets in production | `false` |

## Project Structure

```
ratify/
├── frontend/                # Next.js 15 application
│   ├── app/(auth)/          # Authenticated pages (dashboard, RFCs, admin)
│   ├── app/(public)/        # Public pages (login)
│   ├── components/          # Shared UI components
│   └── lib/                 # API client, auth context, utilities
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── routers/         # API route handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (AI, prompts, settings)
│   │   └── middleware/      # Auth and permission middleware
│   ├── alembic/versions/    # Database migrations
│   └── tests/               # pytest test suite (56 tests)
├── mock-services/
│   ├── mock-oidc/           # Local OIDC identity provider
│   └── mock-jira/           # Local Jira API simulator
├── docker-compose.yml       # Container orchestration
└── .env.example             # Environment variable template
```

## Testing

### Backend Tests (pytest)

```bash
# Run inside the Docker container
docker compose --profile dev exec backend python -m pytest tests/ -x -q --tb=short
```

56 tests covering:
- Mock AI service (vague detection, topic coverage, interview flow)
- Prompt service (defaults, cache, RFC type mapping)
- RFC CRUD, comments, reviews, sign-offs
- Permission enforcement (403 for unauthorized roles)
- Health endpoints

### E2E Tests (Playwright)

Playwright scaffolding is in place for end-to-end browser tests covering health checks, login flow, dashboard, and RFC list.

## Dependencies

### Backend (Python)

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| sqlalchemy[asyncio] | Async ORM |
| asyncpg | PostgreSQL async driver |
| alembic | Database migrations |
| pydantic-settings | Configuration management |
| PyJWT | JWT token handling |
| httpx | Async HTTP client (AI, OIDC, Jira calls) |
| python-multipart | Form data parsing |

### Frontend (Node.js)

| Package | Purpose |
|---------|---------|
| next | React framework |
| react / react-dom | UI library |
| @tanstack/react-table | Data tables |
| tailwindcss | Utility-first CSS |
| lucide-react | Icon library |
| next-themes | Dark/light theme toggle |
| clsx + tailwind-merge | Conditional class utilities |

## Ports

| Service | Port |
|---------|------|
| Frontend | 3100 |
| Backend API | 8000 |
| PostgreSQL | 5500 |
| mock-oidc | 10090 |
| mock-jira | 8543 |

## License

Private -- not licensed for redistribution.
