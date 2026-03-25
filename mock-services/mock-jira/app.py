"""Mock Jira service for local development.

Implements the Jira REST API endpoints that Ratify uses:
- POST /rest/api/2/issue (create issue)
- GET /rest/api/2/issue/{key} (get issue)
- GET /rest/api/2/issue/{key}/transitions (get transitions)
- POST /rest/api/2/issue/{key}/transitions (transition issue)
- GET /rest/api/2/search (JQL search)
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="mock-jira", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
issues: dict[str, dict[str, Any]] = {}
issue_counter = 0
PROJECT_KEY = "RAT"

TRANSITIONS = [
    {"id": "11", "name": "To Do"},
    {"id": "21", "name": "In Progress"},
    {"id": "31", "name": "Done"},
    {"id": "41", "name": "Closed"},
]


def _verify_auth(authorization: str | None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/rest/api/2/issue")
async def create_issue(request: Request, authorization: str | None = Header(None)):
    _verify_auth(authorization)
    global issue_counter
    issue_counter += 1

    body = await request.json()
    fields = body.get("fields", {})

    key = f"{PROJECT_KEY}-{issue_counter}"
    issue_type = fields.get("issuetype", {}).get("name", "Task")
    parent_key = fields.get("parent", {}).get("key")

    issue = {
        "id": str(uuid.uuid4()),
        "key": key,
        "self": f"http://localhost:8543/rest/api/2/issue/{key}",
        "fields": {
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "issuetype": {"name": issue_type},
            "status": {"name": "To Do"},
            "assignee": fields.get("assignee"),
            "parent": {"key": parent_key} if parent_key else None,
            "created": datetime.utcnow().isoformat() + "Z",
            "updated": datetime.utcnow().isoformat() + "Z",
        },
    }
    issues[key] = issue
    return {"id": issue["id"], "key": key, "self": issue["self"]}


@app.get("/rest/api/2/issue/{issue_key}")
async def get_issue(issue_key: str, authorization: str | None = Header(None)):
    _verify_auth(authorization)
    if issue_key not in issues:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    return issues[issue_key]


@app.get("/rest/api/2/issue/{issue_key}/transitions")
async def get_transitions(issue_key: str, authorization: str | None = Header(None)):
    _verify_auth(authorization)
    if issue_key not in issues:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    return {"transitions": TRANSITIONS}


@app.post("/rest/api/2/issue/{issue_key}/transitions")
async def transition_issue(
    issue_key: str, request: Request, authorization: str | None = Header(None)
):
    _verify_auth(authorization)
    if issue_key not in issues:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

    body = await request.json()
    transition_id = body.get("transition", {}).get("id")
    transition = next((t for t in TRANSITIONS if t["id"] == transition_id), None)

    if transition:
        issues[issue_key]["fields"]["status"]["name"] = transition["name"]
        issues[issue_key]["fields"]["updated"] = datetime.utcnow().isoformat() + "Z"

    return {"status": "ok"}


@app.get("/rest/api/2/search")
async def search_issues(
    jql: str = Query(""),
    maxResults: int = Query(50),
    authorization: str | None = Header(None),
):
    _verify_auth(authorization)
    # Simple JQL parsing: just match parent key
    results = []
    for issue in issues.values():
        parent = issue["fields"].get("parent")
        if parent and f'parent = "{parent["key"]}"' in jql:
            results.append(issue)
        elif not jql:
            results.append(issue)
    return {
        "total": len(results),
        "maxResults": maxResults,
        "issues": results[:maxResults],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8543)
