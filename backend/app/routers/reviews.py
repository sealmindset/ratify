import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.review_assignment import ReviewAssignment
from app.models.rfc import RFC
from app.models.sign_off import SignOff
from app.schemas.auth import UserInfo
from app.schemas.review import (
    ReviewAssignmentCreate,
    ReviewAssignmentOut,
    ReviewAssignmentUpdate,
    SignOffCreate,
    SignOffOut,
    SignOffUpdate,
)

router = APIRouter(prefix="/api/rfcs/{rfc_id}/reviews", tags=["reviews"])


def _review_to_out(r: ReviewAssignment) -> ReviewAssignmentOut:
    return ReviewAssignmentOut(
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


def _signoff_to_out(s: SignOff) -> SignOffOut:
    return SignOffOut(
        id=s.id,
        rfc_id=s.rfc_id,
        signer_id=s.signer_id,
        signer_name=s.signer.display_name if s.signer else None,
        team=s.team,
        status=s.status,
        comment=s.comment,
        signed_at=s.signed_at,
        created_at=s.created_at,
    )


# ---------- Review Assignments ----------

@router.get("/", response_model=list[ReviewAssignmentOut])
async def list_reviews(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("reviews", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List review assignments for an RFC."""
    result = await db.execute(
        select(ReviewAssignment)
        .where(ReviewAssignment.rfc_id == rfc_id)
        .order_by(ReviewAssignment.created_at)
    )
    return [_review_to_out(r) for r in result.scalars().all()]


@router.post("/", response_model=ReviewAssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    rfc_id: uuid.UUID,
    data: ReviewAssignmentCreate,
    current_user: UserInfo = Depends(require_permission("reviews", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a review assignment."""
    rfc_result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    if not rfc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="RFC not found")

    review = ReviewAssignment(
        rfc_id=rfc_id,
        section_id=data.section_id,
        reviewer_id=data.reviewer_id,
        team=data.team,
        deadline=data.deadline,
        status="pending",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return _review_to_out(review)


@router.put("/{review_id}", response_model=ReviewAssignmentOut)
async def update_review(
    rfc_id: uuid.UUID,
    review_id: uuid.UUID,
    data: ReviewAssignmentUpdate,
    current_user: UserInfo = Depends(require_permission("reviews", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a review assignment status."""
    result = await db.execute(
        select(ReviewAssignment).where(
            ReviewAssignment.id == review_id, ReviewAssignment.rfc_id == rfc_id
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review assignment not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return _review_to_out(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    rfc_id: uuid.UUID,
    review_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("reviews", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a review assignment."""
    result = await db.execute(
        select(ReviewAssignment).where(
            ReviewAssignment.id == review_id, ReviewAssignment.rfc_id == rfc_id
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review assignment not found")

    await db.delete(review)
    await db.commit()


# ---------- Sign-offs ----------

@router.get("/signoffs", response_model=list[SignOffOut])
async def list_signoffs(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("signoffs", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List sign-offs for an RFC."""
    result = await db.execute(
        select(SignOff).where(SignOff.rfc_id == rfc_id).order_by(SignOff.created_at)
    )
    return [_signoff_to_out(s) for s in result.scalars().all()]


@router.post("/signoffs", response_model=SignOffOut, status_code=status.HTTP_201_CREATED)
async def create_signoff(
    rfc_id: uuid.UUID,
    data: SignOffCreate,
    current_user: UserInfo = Depends(require_permission("signoffs", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Request a sign-off."""
    rfc_result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    if not rfc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="RFC not found")

    signoff = SignOff(
        rfc_id=rfc_id,
        signer_id=data.signer_id,
        team=data.team,
        status="pending",
    )
    db.add(signoff)
    await db.commit()
    await db.refresh(signoff)
    return _signoff_to_out(signoff)


@router.put("/signoffs/{signoff_id}", response_model=SignOffOut)
async def update_signoff(
    rfc_id: uuid.UUID,
    signoff_id: uuid.UUID,
    data: SignOffUpdate,
    current_user: UserInfo = Depends(require_permission("signoffs", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a sign-off (approve/reject)."""
    result = await db.execute(
        select(SignOff).where(SignOff.id == signoff_id, SignOff.rfc_id == rfc_id)
    )
    signoff = result.scalar_one_or_none()
    if not signoff:
        raise HTTPException(status_code=404, detail="Sign-off not found")

    signoff.status = data.status
    signoff.comment = data.comment
    if data.status in ("approved", "rejected"):
        signoff.signed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(signoff)
    return _signoff_to_out(signoff)
