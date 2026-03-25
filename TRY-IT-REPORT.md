# Ratify -- Try-It Report
> Tested: 2026-03-24 9:00 PM CDT
> Status: All Passing

## Summary

Your app was tested automatically. Here's what happened:

| What Was Tested | Result |
|----------------|--------|
| App starts up (5 services) | PASS |
| Login works (4 roles) | PASS |
| All pages load (10 pages) | PASS |
| Permissions work correctly | PASS |
| API is responding (12+ endpoints) | PASS |
| Inline comments (create, reply, resolve) | PASS |
| Prompt management (11 prompts, CRUD) | PASS |
| Activity Logs (52 events captured) | PASS |
| Logout clears session | PASS |

## Login Testing

Each type of user was tested:

| User Type | Login | Dashboard | Permissions | Result |
|-----------|-------|-----------|-------------|--------|
| Super Admin (mock-admin) | PASS | PASS | 48 permissions | PASS |
| Manager (mock-manager) | PASS | PASS | 32 permissions | PASS |
| User (mock-user) | PASS | PASS | 9 permissions | PASS |
| Viewer (mock-viewer) | PASS | PASS | 9 permissions | PASS |

## Pages Tested

| Page | Super Admin | Manager | User | Notes |
|------|-------------|---------|------|-------|
| Dashboard | PASS | PASS | PASS | |
| RFC Registry | PASS | PASS | PASS | 6 RFCs with seed data |
| RFC Detail | PASS | PASS | PASS | 6 sections, inline comments |
| My Reviews | PASS | PASS | PASS | |
| Admin - Users | PASS | N/A | N/A | Admin only |
| Admin - Roles | PASS | N/A | N/A | Admin only |
| Admin - Settings | PASS | N/A | N/A | Admin only |
| Admin - AI Prompts | PASS | N/A | N/A | Admin only, 11 prompts |
| Admin - Activity Logs | PASS | N/A | N/A | Admin only |

## New Features Tested

### Inline Document Comments
- Create inline comment with quoted text anchor: PASS
- Reply to inline comment (threaded): PASS
- Resolve comment: PASS
- Unresolve comment: PASS
- Threaded comment tree returned correctly: PASS

### Prompt Management (Tier 2)
- List all 11 managed prompts: PASS
- Get prompt detail with version history: PASS
- Test prompt preview with token estimate: PASS
- Prompts grouped by category (Interview, Generation, Refinement, Assistance): PASS
- Cache with 60s TTL + code fallback: Active

### Activity Logs
- Stats endpoint (buffer: 10,000, used: 52, errors: 2): PASS
- Events endpoint (captures inbound + outbound): PASS
- Permission gating (User role blocked): PASS

## Permission Boundaries

| Endpoint | User Role | Expected | Result |
|----------|-----------|----------|--------|
| GET /api/admin/prompts/ | User | 403 | PASS |
| GET /api/users/ | User | 403 | PASS |
| GET /api/roles/ | User | 403 | PASS |
| GET /api/admin/logs/stats | User | 403 | PASS |
| GET /api/rfcs/ | User | 200 | PASS |
| GET /api/my-reviews/ | User | 200 | PASS |

## How to Access Your App

- **Open your browser to:** http://localhost:3100
- **To log in as Super Admin:** Click "Sign In", pick "Admin User" from the login screen
- **To log in as Manager:** Click "Sign In", pick "Manager User" from the login screen
- **To log in as User:** Click "Sign In", pick "Regular User" from the login screen
- **To log in as Viewer:** Click "Sign In", pick "Viewer User" from the login screen

## Services Running

| Service | Port | Status |
|---------|------|--------|
| Frontend (Next.js) | 3100 | Healthy |
| Backend (FastAPI) | 8000 | Healthy |
| PostgreSQL | 5500 | Healthy |
| Mock OIDC | 10090 | Healthy |
| Mock Jira | 8543 | Healthy |

## Issues Found
None -- all tests passed.

## What to Do Next
- Explore your app in the browser (see instructions above)
- If something doesn't look right, tell me and I'll fix it
- When you're happy with how it works, type **/ship-it** to deploy
- To make changes, type **/resume-it**
