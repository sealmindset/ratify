import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.permissions import require_permission
from app.models.ai_conversation import AIConversation
from app.models.rfc import RFC
from app.models.rfc_section import RFCSection
from app.models.comment import Comment
from app.schemas.ai import (
    AICommentAssistRequest,
    AIInterviewMessage,
    AIInterviewStart,
    AIRefineRequest,
    AIResponse,
)
from app.schemas.auth import UserInfo
from app.services import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/interview/start", response_model=AIResponse)
async def start_interview(
    data: AIInterviewStart,
    current_user: UserInfo = Depends(require_permission("ai", "interview")),
    db: AsyncSession = Depends(get_db),
):
    """Start an AI interview to create a new RFC."""
    from sqlalchemy import func

    # Create the RFC
    max_num = await db.execute(select(func.max(RFC.rfc_number)))
    next_num = (max_num.scalar() or 0) + 1

    rfc = RFC(
        title=data.title,
        rfc_type=data.rfc_type,
        rfc_number=next_num,
        author_id=uuid.UUID(current_user.user_id),
        status="draft",
    )
    db.add(rfc)
    await db.flush()

    # Start the conversation
    initial_messages = json.dumps([])
    updated_messages, ai_response, topics_covered, topics_total, current_topic = (
        await ai_service.interview_next(
            initial_messages,
            data.rfc_type,
            f"I want to create an RFC titled '{data.title}' of type '{data.rfc_type}'. Please start the interview.",
            db,
        )
    )

    conversation = AIConversation(
        rfc_id=rfc.id,
        rfc_type=data.rfc_type,
        messages_json=updated_messages,
        status="active",
    )
    db.add(conversation)
    await db.commit()

    return AIResponse(
        message=ai_response,
        conversation_id=conversation.id,
        rfc_id=rfc.id,
        topics_covered=topics_covered,
        topics_total=topics_total,
        current_topic=current_topic,
    )


@router.post("/interview/{conversation_id}/message", response_model=AIResponse)
async def continue_interview(
    conversation_id: uuid.UUID,
    data: AIInterviewMessage,
    current_user: UserInfo = Depends(require_permission("ai", "interview")),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in an ongoing interview."""
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updated_messages, ai_response, topics_covered, topics_total, current_topic = (
        await ai_service.interview_next(
            conversation.messages_json,
            conversation.rfc_type,
            data.message,
            db,
        )
    )
    conversation.messages_json = updated_messages

    # Check if interview is complete
    sections_generated = False
    if "INTERVIEW_COMPLETE" in ai_response:
        conversation.status = "completed"
        # Generate RFC sections
        sections = await ai_service.generate_sections(
            updated_messages, conversation.rfc_type, db
        )
        for i, section_data in enumerate(sections):
            section = RFCSection(
                rfc_id=conversation.rfc_id,
                title=section_data.get("title", f"Section {i + 1}"),
                content=section_data.get("content", ""),
                section_type=section_data.get("section_type", "body"),
                order=section_data.get("order", i + 1),
            )
            db.add(section)
        sections_generated = True

    await db.commit()

    return AIResponse(
        message=ai_response,
        conversation_id=conversation.id,
        rfc_id=conversation.rfc_id,
        sections_generated=sections_generated,
        topics_covered=topics_covered,
        topics_total=topics_total,
        current_topic=current_topic,
    )


@router.post("/refine", response_model=AIResponse)
async def refine_section(
    data: AIRefineRequest,
    current_user: UserInfo = Depends(require_permission("ai", "refine")),
    db: AsyncSession = Depends(get_db),
):
    """Refine an RFC section using AI."""
    result = await db.execute(
        select(RFCSection).where(RFCSection.id == data.section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    refined = await ai_service.refine_section(section.content or "", data.instruction, db)
    section.content = refined
    await db.commit()

    return AIResponse(message=refined, rfc_id=section.rfc_id)


@router.post("/assist-comment", response_model=AIResponse)
async def assist_comment(
    data: AICommentAssistRequest,
    current_user: UserInfo = Depends(require_permission("ai", "refine")),
    db: AsyncSession = Depends(get_db),
):
    """Help the author draft a response to a comment."""
    result = await db.execute(select(Comment).where(Comment.id == data.comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    section_content = None
    if comment.section_id:
        section_result = await db.execute(
            select(RFCSection).where(RFCSection.id == comment.section_id)
        )
        section = section_result.scalar_one_or_none()
        if section:
            section_content = section.content

    response = await ai_service.assist_comment_response(
        comment.content, section_content, data.instruction, db
    )
    return AIResponse(message=response, rfc_id=comment.rfc_id)
