import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_id: uuid.UUID
    rfc_type: str
    messages_json: str
    status: str
    created_at: datetime
    updated_at: datetime


class AIInterviewStart(BaseModel):
    title: str
    rfc_type: str = "other"


class AIInterviewMessage(BaseModel):
    message: str


class AIRefineRequest(BaseModel):
    section_id: uuid.UUID
    instruction: str


class AICommentAssistRequest(BaseModel):
    comment_id: uuid.UUID
    instruction: str | None = None


class AIResponse(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    rfc_id: uuid.UUID | None = None
    sections_generated: bool = False
