"""Integration tests for AI interview endpoints."""

import pytest


@pytest.mark.asyncio
async def test_start_interview(admin_client, db_session):
    resp = await admin_client.post("/api/ai/interview/start", json={
        "title": "New Infrastructure Proposal",
        "rfc_type": "infrastructure",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]  # AI greeting
    assert data["conversation_id"] is not None
    assert data["rfc_id"] is not None
    assert data["topics_total"] == 8
    assert data["current_topic"] is not None
    assert isinstance(data["topics_covered"], list)


@pytest.mark.asyncio
async def test_continue_interview(admin_client, db_session):
    # Start
    start_resp = await admin_client.post("/api/ai/interview/start", json={
        "title": "Security Review",
        "rfc_type": "security",
    })
    conv_id = start_resp.json()["conversation_id"]

    # Continue with a substantive answer
    resp = await admin_client.post(f"/api/ai/interview/{conv_id}/message", json={
        "message": "We have a SQL injection vulnerability in the legacy authentication module. "
                   "The main threat vectors are through the login form and the API token endpoint."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]
    assert data["conversation_id"] == conv_id
    assert data["topics_total"] == 8


@pytest.mark.asyncio
async def test_interview_conversation_not_found(admin_client, db_session):
    resp = await admin_client.post(
        "/api/ai/interview/00000000-0000-0000-0000-999999999999/message",
        json={"message": "hello"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_viewer_cannot_start_interview(viewer_client, db_session):
    """Viewer doesn't have ai.interview permission."""
    resp = await viewer_client.post("/api/ai/interview/start", json={
        "title": "Should Fail",
        "rfc_type": "other",
    })
    assert resp.status_code == 403
