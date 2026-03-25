import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.JIRA_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }


def _url(path: str) -> str:
    return f"{settings.JIRA_BASE_URL}{path}"


async def create_epic(title: str, description: str) -> dict:
    """Create a Jira Epic for an RFC."""
    payload = {
        "fields": {
            "summary": title,
            "description": description,
            "issuetype": {"name": "Epic"},
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_url("/rest/api/2/issue"), json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def create_subtask(
    epic_key: str, summary: str, description: str, assignee_email: str | None = None
) -> dict:
    """Create a sub-task under an Epic."""
    payload = {
        "fields": {
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Sub-task"},
            "parent": {"key": epic_key},
        }
    }
    if assignee_email:
        payload["fields"]["assignee"] = {"emailAddress": assignee_email}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_url("/rest/api/2/issue"), json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def get_issue(issue_key: str) -> dict:
    """Get a Jira issue by key."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(_url(f"/rest/api/2/issue/{issue_key}"), headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def transition_issue(issue_key: str, transition_name: str) -> bool:
    """Transition a Jira issue to a new status."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get available transitions
        resp = await client.get(
            _url(f"/rest/api/2/issue/{issue_key}/transitions"), headers=_headers()
        )
        resp.raise_for_status()
        transitions = resp.json().get("transitions", [])

        target = next(
            (t for t in transitions if t["name"].lower() == transition_name.lower()),
            None,
        )
        if not target:
            logger.warning(f"Transition '{transition_name}' not found for {issue_key}")
            return False

        resp = await client.post(
            _url(f"/rest/api/2/issue/{issue_key}/transitions"),
            json={"transition": {"id": target["id"]}},
            headers=_headers(),
        )
        resp.raise_for_status()
        return True


async def search_issues(jql: str, max_results: int = 50) -> list[dict]:
    """Search for issues using JQL."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            _url("/rest/api/2/search"),
            params={"jql": jql, "maxResults": max_results},
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("issues", [])
