"""Integration tests for comment endpoints."""

import pytest

from tests.conftest import ADMIN_USER


@pytest.mark.asyncio
async def test_comment_crud(admin_client, db_session):
    # Create an RFC first
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Commented RFC"})
    rfc_id = rfc_resp.json()["id"]

    # Create a comment
    resp = await admin_client.post(f"/api/rfcs/{rfc_id}/comments/", json={
        "content": "This looks good!",
        "references": [],
    })
    assert resp.status_code == 201
    comment = resp.json()
    assert comment["content"] == "This looks good!"
    assert comment["author_name"] == "Admin User"
    assert comment["is_resolved"] is False
    comment_id = comment["id"]

    # List comments
    list_resp = await admin_client.get(f"/api/rfcs/{rfc_id}/comments/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Update comment
    update_resp = await admin_client.put(f"/api/rfcs/{rfc_id}/comments/{comment_id}", json={
        "content": "Updated: this looks great!",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated: this looks great!"

    # Delete comment
    del_resp = await admin_client.delete(f"/api/rfcs/{rfc_id}/comments/{comment_id}")
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_comment_resolve_unresolve(admin_client, db_session):
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Resolve Test"})
    rfc_id = rfc_resp.json()["id"]

    comment_resp = await admin_client.post(f"/api/rfcs/{rfc_id}/comments/", json={
        "content": "Needs fix",
        "references": [],
    })
    comment_id = comment_resp.json()["id"]

    # Resolve
    resolve_resp = await admin_client.patch(f"/api/rfcs/{rfc_id}/comments/{comment_id}/resolve")
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["is_resolved"] is True
    assert resolve_resp.json()["resolved_by"] is not None

    # Unresolve
    unresolve_resp = await admin_client.patch(f"/api/rfcs/{rfc_id}/comments/{comment_id}/unresolve")
    assert unresolve_resp.status_code == 200
    assert unresolve_resp.json()["is_resolved"] is False
    assert unresolve_resp.json()["resolved_by"] is None


@pytest.mark.asyncio
async def test_threaded_comments(admin_client, db_session):
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Thread Test"})
    rfc_id = rfc_resp.json()["id"]

    # Top-level comment
    parent_resp = await admin_client.post(f"/api/rfcs/{rfc_id}/comments/", json={
        "content": "Top-level comment",
        "references": [],
    })
    parent_id = parent_resp.json()["id"]

    # Reply
    reply_resp = await admin_client.post(f"/api/rfcs/{rfc_id}/comments/", json={
        "content": "This is a reply",
        "parent_id": parent_id,
        "references": [],
    })
    assert reply_resp.status_code == 201

    # List -- should return 1 top-level with 1 reply nested
    list_resp = await admin_client.get(f"/api/rfcs/{rfc_id}/comments/")
    threads = list_resp.json()
    assert len(threads) == 1  # One top-level
    assert len(threads[0]["replies"]) == 1
    assert threads[0]["replies"][0]["content"] == "This is a reply"


@pytest.mark.asyncio
async def test_inline_comment_with_anchor(admin_client, db_session):
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Inline Test"})
    rfc_id = rfc_resp.json()["id"]

    resp = await admin_client.post(f"/api/rfcs/{rfc_id}/comments/", json={
        "content": "This phrase needs clarification",
        "quoted_text": "the proposed solution",
        "anchor_offset": 42,
        "anchor_length": 21,
        "references": [],
    })
    assert resp.status_code == 201
    assert resp.json()["quoted_text"] == "the proposed solution"
    assert resp.json()["anchor_offset"] == 42
