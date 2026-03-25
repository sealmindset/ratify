"""Integration tests for RFC CRUD endpoints."""

import pytest

from tests.conftest import ADMIN_USER


@pytest.mark.asyncio
async def test_create_rfc(admin_client, db_session):
    resp = await admin_client.post("/api/rfcs/", json={
        "title": "New Microservice Architecture",
        "summary": "Proposal to split monolith",
        "rfc_type": "architecture",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Microservice Architecture"
    assert data["rfc_type"] == "architecture"
    assert data["status"] == "draft"
    assert data["rfc_number"] == 1
    assert data["author_name"] == "Admin User"


@pytest.mark.asyncio
async def test_list_rfcs(admin_client, db_session):
    # Create two RFCs
    await admin_client.post("/api/rfcs/", json={"title": "RFC 1", "rfc_type": "security"})
    await admin_client.post("/api/rfcs/", json={"title": "RFC 2", "rfc_type": "infrastructure"})

    resp = await admin_client.get("/api/rfcs/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Ordered by rfc_number desc
    assert data[0]["title"] == "RFC 2"
    assert data[1]["title"] == "RFC 1"


@pytest.mark.asyncio
async def test_list_rfcs_filter_by_status(admin_client, db_session):
    await admin_client.post("/api/rfcs/", json={"title": "Draft RFC"})
    resp = await admin_client.get("/api/rfcs/", params={"status": "draft"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await admin_client.get("/api/rfcs/", params={"status": "approved"})
    assert resp.status_code == 200
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_get_rfc(admin_client, db_session):
    create_resp = await admin_client.post("/api/rfcs/", json={
        "title": "Get Test",
        "rfc_type": "data",
    })
    rfc_id = create_resp.json()["id"]

    resp = await admin_client.get(f"/api/rfcs/{rfc_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Test"
    assert resp.json()["sections"] == []


@pytest.mark.asyncio
async def test_get_rfc_not_found(admin_client, db_session):
    resp = await admin_client.get("/api/rfcs/00000000-0000-0000-0000-999999999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_rfc(admin_client, db_session):
    create_resp = await admin_client.post("/api/rfcs/", json={"title": "Original"})
    rfc_id = create_resp.json()["id"]

    resp = await admin_client.put(f"/api/rfcs/{rfc_id}", json={
        "title": "Updated Title",
        "status": "in_review",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["status"] == "in_review"


@pytest.mark.asyncio
async def test_delete_rfc(admin_client, db_session):
    create_resp = await admin_client.post("/api/rfcs/", json={"title": "To Delete"})
    rfc_id = create_resp.json()["id"]

    resp = await admin_client.delete(f"/api/rfcs/{rfc_id}")
    assert resp.status_code == 204

    # Verify gone
    resp = await admin_client.get(f"/api/rfcs/{rfc_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_and_update_section(admin_client, db_session):
    create_resp = await admin_client.post("/api/rfcs/", json={"title": "With Sections"})
    rfc_id = create_resp.json()["id"]

    # Create section
    sec_resp = await admin_client.post(f"/api/rfcs/{rfc_id}/sections", json={
        "title": "Background",
        "content": "Some background info",
        "section_type": "background",
        "order": 1,
    })
    assert sec_resp.status_code == 201
    sec_id = sec_resp.json()["id"]
    assert sec_resp.json()["title"] == "Background"

    # Update section
    update_resp = await admin_client.put(f"/api/rfcs/{rfc_id}/sections/{sec_id}", json={
        "content": "Updated background info",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated background info"

    # Delete section
    del_resp = await admin_client.delete(f"/api/rfcs/{rfc_id}/sections/{sec_id}")
    assert del_resp.status_code == 204
