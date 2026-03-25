"""Integration tests for permission enforcement (403 for unauthorized actions)."""

import pytest

from tests.conftest import ADMIN_USER, REGULAR_USER, VIEWER_USER, seed_user, _make_client


@pytest.mark.asyncio
async def test_viewer_cannot_create_rfc(viewer_client, db_session):
    """Viewer has rfcs.read but NOT rfcs.create."""
    resp = await viewer_client.post("/api/rfcs/", json={
        "title": "Should Fail",
        "rfc_type": "other",
    })
    assert resp.status_code == 403
    assert "Permission denied" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_viewer_can_list_rfcs(viewer_client, db_session):
    """Viewer can read RFC list (even if empty)."""
    resp = await viewer_client.get("/api/rfcs/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_regular_user_can_create_rfc(user_client, db_session):
    """Regular user has rfcs.create permission."""
    resp = await user_client.post("/api/rfcs/", json={
        "title": "User Created RFC",
        "rfc_type": "process",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "User Created RFC"


@pytest.mark.asyncio
async def test_regular_user_cannot_delete_rfc(db_session):
    """Regular user has rfcs.create and rfcs.read but NOT rfcs.delete."""
    await seed_user(db_session, ADMIN_USER)
    await seed_user(db_session, REGULAR_USER)

    # Create as admin
    async with _make_client(db_session, ADMIN_USER) as admin:
        create_resp = await admin.post("/api/rfcs/", json={"title": "No Delete"})
        rfc_id = create_resp.json()["id"]

    # Try to delete as regular user
    async with _make_client(db_session, REGULAR_USER) as user:
        resp = await user.delete(f"/api/rfcs/{rfc_id}")
        assert resp.status_code == 403

    from app.main import _fastapi_app as app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_viewer_cannot_create_comment(db_session):
    """Viewer has comments.read but NOT comments.create."""
    await seed_user(db_session, ADMIN_USER)
    await seed_user(db_session, VIEWER_USER)

    # Create RFC as admin
    async with _make_client(db_session, ADMIN_USER) as admin:
        rfc_resp = await admin.post("/api/rfcs/", json={"title": "Comment Test"})
        rfc_id = rfc_resp.json()["id"]

    # Try to comment as viewer
    async with _make_client(db_session, VIEWER_USER) as viewer:
        resp = await viewer.post(f"/api/rfcs/{rfc_id}/comments/", json={
            "content": "Should fail",
            "references": [],
        })
        assert resp.status_code == 403

    from app.main import _fastapi_app as app
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_viewer_cannot_create_review(db_session):
    """Viewer cannot create review assignments."""
    await seed_user(db_session, ADMIN_USER)
    await seed_user(db_session, VIEWER_USER)

    async with _make_client(db_session, ADMIN_USER) as admin:
        rfc_resp = await admin.post("/api/rfcs/", json={"title": "Review Perm Test"})
        rfc_id = rfc_resp.json()["id"]

    async with _make_client(db_session, VIEWER_USER) as viewer:
        resp = await viewer.post(f"/api/rfcs/{rfc_id}/reviews/", json={
            "reviewer_id": "00000000-0000-0000-0000-000000000004",
            "team": "Test",
        })
        assert resp.status_code == 403

    from app.main import _fastapi_app as app
    app.dependency_overrides.clear()
