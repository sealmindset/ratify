"""Integration tests for review assignment and sign-off endpoints."""

import pytest

from tests.conftest import ADMIN_USER


@pytest.mark.asyncio
async def test_review_assignment_crud(admin_client, db_session):
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Review Test"})
    rfc_id = rfc_resp.json()["id"]

    # Create review assignment
    resp = await admin_client.post(f"/api/rfcs/{rfc_id}/reviews/", json={
        "reviewer_id": ADMIN_USER.user_id,
        "team": "Engineering",
    })
    assert resp.status_code == 201
    review = resp.json()
    assert review["team"] == "Engineering"
    assert review["status"] == "pending"
    review_id = review["id"]

    # List reviews
    list_resp = await admin_client.get(f"/api/rfcs/{rfc_id}/reviews/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Update review
    update_resp = await admin_client.put(f"/api/rfcs/{rfc_id}/reviews/{review_id}", json={
        "status": "completed",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "completed"

    # Delete review
    del_resp = await admin_client.delete(f"/api/rfcs/{rfc_id}/reviews/{review_id}")
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_signoff_crud(admin_client, db_session):
    rfc_resp = await admin_client.post("/api/rfcs/", json={"title": "Signoff Test"})
    rfc_id = rfc_resp.json()["id"]

    # Create sign-off
    resp = await admin_client.post(f"/api/rfcs/{rfc_id}/reviews/signoffs", json={
        "signer_id": ADMIN_USER.user_id,
        "team": "Security",
    })
    assert resp.status_code == 201
    signoff = resp.json()
    assert signoff["team"] == "Security"
    assert signoff["status"] == "pending"
    signoff_id = signoff["id"]

    # List sign-offs
    list_resp = await admin_client.get(f"/api/rfcs/{rfc_id}/reviews/signoffs")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Approve sign-off
    update_resp = await admin_client.put(f"/api/rfcs/{rfc_id}/reviews/signoffs/{signoff_id}", json={
        "status": "approved",
        "comment": "LGTM",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "approved"
    assert update_resp.json()["signed_at"] is not None
