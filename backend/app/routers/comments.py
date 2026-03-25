import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.comment import Comment
from app.models.reference import Reference
from app.models.rfc import RFC
from app.schemas.auth import UserInfo
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate, ReferenceOut

router = APIRouter(prefix="/api/rfcs/{rfc_id}/comments", tags=["comments"])


def _comment_to_out(comment: Comment, replies: list["CommentOut"] | None = None) -> CommentOut:
    return CommentOut(
        id=comment.id,
        rfc_id=comment.rfc_id,
        section_id=comment.section_id,
        author_id=comment.author_id,
        author_name=comment.author.display_name if comment.author else None,
        content=comment.content,
        parent_id=comment.parent_id,
        quoted_text=comment.quoted_text,
        anchor_offset=comment.anchor_offset,
        anchor_length=comment.anchor_length,
        is_resolved=comment.is_resolved,
        resolved_by=comment.resolved_by,
        resolved_by_name=comment.resolver.display_name if comment.resolver else None,
        resolved_at=comment.resolved_at,
        replies=replies or [],
        references=[
            ReferenceOut.model_validate(r) for r in (comment.references or [])
        ],
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def _build_thread_tree(comments: list[Comment]) -> list[CommentOut]:
    """Build threaded comment tree -- top-level comments with nested replies."""
    by_id: dict[uuid.UUID, Comment] = {c.id: c for c in comments}
    reply_map: dict[uuid.UUID, list[Comment]] = {}

    for c in comments:
        if c.parent_id:
            reply_map.setdefault(c.parent_id, []).append(c)

    def build_replies(parent_id: uuid.UUID) -> list[CommentOut]:
        children = reply_map.get(parent_id, [])
        return [_comment_to_out(child, build_replies(child.id)) for child in children]

    # Top-level = comments with no parent
    roots = [c for c in comments if c.parent_id is None]
    return [_comment_to_out(root, build_replies(root.id)) for root in roots]


@router.get("/", response_model=list[CommentOut])
async def list_comments(
    rfc_id: uuid.UUID,
    section_id: uuid.UUID | None = None,
    current_user: UserInfo = Depends(require_permission("comments", "read")),
    db: AsyncSession = Depends(get_db),
):
    """List comments for an RFC, optionally filtered by section. Returns threaded tree."""
    query = select(Comment).where(Comment.rfc_id == rfc_id).order_by(Comment.created_at)
    if section_id:
        query = query.where(Comment.section_id == section_id)

    result = await db.execute(query)
    comments = list(result.scalars().all())
    return _build_thread_tree(comments)


@router.post("/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    rfc_id: uuid.UUID,
    data: CommentCreate,
    current_user: UserInfo = Depends(require_permission("comments", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment to an RFC (optionally inline on a section)."""
    # Verify RFC exists
    rfc_result = await db.execute(select(RFC).where(RFC.id == rfc_id))
    if not rfc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="RFC not found")

    comment = Comment(
        rfc_id=rfc_id,
        section_id=data.section_id,
        author_id=uuid.UUID(current_user.user_id),
        content=data.content,
        parent_id=data.parent_id,
        quoted_text=data.quoted_text,
        anchor_offset=data.anchor_offset,
        anchor_length=data.anchor_length,
    )
    db.add(comment)
    await db.flush()

    # Add references
    for ref_data in data.references:
        ref = Reference(
            comment_id=comment.id,
            url=ref_data.url,
            title=ref_data.title,
            ref_type=ref_data.ref_type,
        )
        db.add(ref)

    await db.commit()
    await db.refresh(comment)
    return _comment_to_out(comment)


@router.put("/{comment_id}", response_model=CommentOut)
async def update_comment(
    rfc_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    current_user: UserInfo = Depends(require_permission("comments", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a comment."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.rfc_id == rfc_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if str(comment.author_id) != current_user.user_id:
        raise HTTPException(status_code=403, detail="Can only edit your own comments")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)

    await db.commit()
    await db.refresh(comment)
    return _comment_to_out(comment)


@router.patch("/{comment_id}/resolve", response_model=CommentOut)
async def resolve_comment(
    rfc_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("comments", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a comment as resolved."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.rfc_id == rfc_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_resolved = True
    comment.resolved_by = uuid.UUID(current_user.user_id)
    comment.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(comment)
    return _comment_to_out(comment)


@router.patch("/{comment_id}/unresolve", response_model=CommentOut)
async def unresolve_comment(
    rfc_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("comments", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Re-open a resolved comment."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.rfc_id == rfc_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.is_resolved = False
    comment.resolved_by = None
    comment.resolved_at = None

    await db.commit()
    await db.refresh(comment)
    return _comment_to_out(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    rfc_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: UserInfo = Depends(require_permission("comments", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a comment."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.rfc_id == rfc_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(comment)
    await db.commit()
