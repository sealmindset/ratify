import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.review_assignment import ReviewAssignment
from app.schemas.auth import UserInfo
from app.schemas.review import ReviewAssignmentOut

router = APIRouter(prefix="/api/my-reviews", tags=["my-reviews"])


@router.get("/", response_model=list[ReviewAssignmentOut])
async def list_my_reviews(
    status_filter: str | None = Query(None, alias="status"),
    current_user: UserInfo = Depends(require_permission("reviews", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's review assignments."""
    query = (
        select(ReviewAssignment)
        .where(ReviewAssignment.reviewer_id == uuid.UUID(current_user.user_id))
        .order_by(ReviewAssignment.deadline.asc().nullslast(), ReviewAssignment.created_at.desc())
    )
    if status_filter:
        query = query.where(ReviewAssignment.status == status_filter)

    result = await db.execute(query)
    reviews = result.scalars().all()
    return [
        ReviewAssignmentOut(
            id=r.id,
            rfc_id=r.rfc_id,
            section_id=r.section_id,
            reviewer_id=r.reviewer_id,
            reviewer_name=r.reviewer.display_name if r.reviewer else None,
            team=r.team,
            status=r.status,
            deadline=r.deadline,
            jira_task_key=r.jira_task_key,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in reviews
    ]
