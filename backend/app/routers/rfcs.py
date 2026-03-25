import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.comment import Comment
from app.models.review_assignment import ReviewAssignment
from app.models.rfc import RFC
from app.models.rfc_section import RFCSection
from app.schemas.auth import UserInfo
from app.schemas.rfc import (
    RFCCreate,
    RFCListOut,
    RFCOut,
    RFCSectionCreate,
    RFCSectionOut,
    RFCSectionUpdate,
    RFCUpdate,
)

router = APIRouter(prefix="/api/rfcs", tags=["rfcs"])


def _rfc_to_list_out(rfc: RFC, comment_count: int = 0, review_count: int = 0) -> RFCListOut:
    return RFCListOut(
        id=rfc.id,
        rfc_number=rfc.rfc_number,
        title=rfc.title,
        summary=rfc.summary,
        rfc_type=rfc.rfc_type,
        status=rfc.status,
        author_id=rfc.author_id,
        author_name=rfc.author.display_name if rfc.author else None,
        jira_epic_key=rfc.jira_epic_key,
        comment_count=comment_count,
        review_count=review_count,
        created_at=rfc.created_at,
        updated_at=rfc.updated_at,
    )


def _rfc_to_out(rfc: RFC) -> RFCOut:
    return RFCOut(
        id=rfc.id,
        rfc_number=rfc.rfc_number,
        title=rfc.title,
        summary=rfc.summary,
        rfc_type=rfc.rfc_type,
        status=rfc.status,
        author_id=rfc.author_id,
        author_name=rfc.author.display_name if rfc.author else None,
        jira_epic_key=rfc.jira_epic_key,
        sections=[
            RFCSectionOut(
                id=s.id, rfc_id=s.rfc_id, title=s.title, content=s.content,
                section_type=s.section_type, order=s.order,
                created_at=s.created_at, updated_at=s.updated_at,
            )
            for s in (rfc.sections or [])
        ],
        created_at=rfc.created_at,
        updated_at=rfc.updated_at,
    )


# ---------- RFC CRUD ----------

@router.get("/", response_model=list[RFCListOut])
async def list_rfcs(
    status_filter: str | None = Query(None, alias="status"),
    rfc_type: str | None = None,
    current_user: UserInfo = Depends(require_permission("rfcs", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List all RFCs with optional filters."""
    query = select(RFC).order_by(RFC.rfc_number.desc())
    if status_filter:
        query = query.where(RFC.status == status_filter)
    if rfc_type:
        query = query.where(RFC.rfc_type == rfc_type)

    result = await db.execute(query)
    rfcs = result.scalars().all()

    # Get counts
    out = []
    for rfc in rfcs:
        comment_count_result = await db.execute(
            select(func.count()).select_from(Comment).where(Comment.rfc_id == rfc.id)
        )
        review_count_result = await db.execute(
            select(func.count()).select_from(ReviewAssignment).where(ReviewAssignment.rfc_id == rfc.id)
        )
        out.append(_rfc_to_list_out(
            rfc,
            comment_count=comment_count_result.scalar() or 0,
            review_count=review_count_result.scalar() or 0,
        ))
    return out


@router.post("/", response_model=RFCOut, status_code=status.HTTP_201_CREATED)
async def create_rfc(
    data: RFCCreate,
    current_user: UserInfo = Depends(require_permission("rfcs", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new RFC."""
    # Get next rfc_number
    max_num = await db.execute(select(func.max(RFC.rfc_number)))
    next_num = (max_num.scalar() or 0) + 1

    rfc = RFC(
        title=data.title,
        summary=data.summary,
        rfc_type=data.rfc_type,
        rfc_number=next_num,
        author_id=uuid.UUID(current_user.user_id),
        status="draft",
    )
    db.add(rfc)
    await db.commit()
    await db.refresh(rfc)
    return _rfc_to_out(rfc)


@router.get("/{rfc_id}", response_model=RFCOut)
async def get_rfc(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("rfcs", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single RFC with all sections."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")
    return _rfc_to_out(rfc)


@router.put("/{rfc_id}", response_model=RFCOut)
async def update_rfc(
    rfc_id: uuid.UUID,
    data: RFCUpdate,
    current_user: UserInfo = Depends(require_permission("rfcs", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an RFC."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rfc, field, value)

    await db.commit()
    await db.refresh(rfc)
    return _rfc_to_out(rfc)


@router.delete("/{rfc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rfc(
    rfc_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("rfcs", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an RFC and all related data."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    rfc = result.scalar_one_or_none()
    if not rfc:
        raise HTTPException(status_code=404, detail="RFC not found")

    await db.delete(rfc)
    await db.commit()


# ---------- RFC Sections ----------

@router.post("/{rfc_id}/sections", response_model=RFCSectionOut, status_code=status.HTTP_201_CREATED)
async def create_section(
    rfc_id: uuid.UUID,
    data: RFCSectionCreate,
    current_user: UserInfo = Depends(require_permission("rfcs.sections", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Add a section to an RFC."""
    result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="RFC not found")

    section = RFCSection(rfc_id=rfc_id, **data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return RFCSectionOut.model_validate(section)


@router.put("/{rfc_id}/sections/{section_id}", response_model=RFCSectionOut)
async def update_section(
    rfc_id: uuid.UUID,
    section_id: uuid.UUID,
    data: RFCSectionUpdate,
    current_user: UserInfo = Depends(require_permission("rfcs.sections", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an RFC section."""
    result = await db.execute(
        select(RFCSection).where(RFCSection.id == section_id, RFCSection.rfc_id == rfc_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)
    return RFCSectionOut.model_validate(section)


@router.delete("/{rfc_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    rfc_id: uuid.UUID,
    section_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("rfcs.sections", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an RFC section."""
    result = await db.execute(
        select(RFCSection).where(RFCSection.id == section_id, RFCSection.rfc_id == rfc_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    await db.delete(section)
    await db.commit()
