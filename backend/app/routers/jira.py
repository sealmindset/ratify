import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.review_assignment import ReviewAssignment
from app.models.rfc import RFC
from app.models.rfc_section import RFCSection
from app.schemas.auth import UserInfo
from app.services import jira_service

router = APIRouter(prefix="/api/rfcs/{rfc_id}/jira", tags=["jira"])


@router.post("/sync")
async def sync_to_jira(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("jira", "sync")),
    db: AsyncSession = Depends(get_db),
):
    """Create/sync Jira Epic and tasks for an RFC."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    # Create Epic if not exists
    if not rfc.jira_epic_key:
        epic = await jira_service.create_epic(
            title=f"RFC-{rfc.rfc_number}: {rfc.title}",
            description=rfc.summary or rfc.title,
        )
        rfc.jira_epic_key = epic["key"]
        await db.flush()

    # Create sub-tasks for review assignments without Jira keys
    reviews_result = await db.execute(
        select(ReviewAssignment).where(
            ReviewAssignment.rfc_id == rfc_id,
            ReviewAssignment.jira_task_key.is_(None),
        )
    )
    reviews = reviews_result.scalars().all()

    for review in reviews:
        section_title = "Full RFC"
        if review.section_id:
            section_result = await db.execute(
                select(RFCSection).where(RFCSection.id == review.section_id)
            )
            section = section_result.scalar_one_or_none()
            if section:
                section_title = section.title

        reviewer_name = review.reviewer.display_name if review.reviewer else "Unassigned"
        task = await jira_service.create_subtask(
            epic_key=rfc.jira_epic_key,
            summary=f"Review: {section_title} ({review.team})",
            description=f"Review assignment for {reviewer_name} on RFC-{rfc.rfc_number}",
            assignee_email=review.reviewer.email if review.reviewer else None,
        )
        review.jira_task_key = task["key"]

    await db.commit()

    return {
        "epic_key": rfc.jira_epic_key,
        "tasks_created": len(reviews),
    }


@router.get("/status")
async def get_jira_status(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("jira", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get Jira sync status for an RFC."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    if not rfc.jira_epic_key:
        return {"synced": False, "epic_key": None, "tasks": []}

    try:
        epic = await jira_service.get_issue(rfc.jira_epic_key)
        tasks = await jira_service.search_issues(
            f'parent = "{rfc.jira_epic_key}"'
        )
        return {
            "synced": True,
            "epic_key": rfc.jira_epic_key,
            "epic_status": epic.get("fields", {}).get("status", {}).get("name"),
            "tasks": [
                {
                    "key": t["key"],
                    "summary": t["fields"]["summary"],
                    "status": t["fields"]["status"]["name"],
                }
                for t in tasks
            ],
        }
    except Exception:
        return {"synced": True, "epic_key": rfc.jira_epic_key, "tasks": [], "error": "Could not fetch Jira data"}
