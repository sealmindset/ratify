import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    comment_id: uuid.UUID
    url: str
    title: str
    ref_type: str
    created_at: datetime


class ReferenceCreate(BaseModel):
    url: str
    title: str
    ref_type: str = "link"


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_id: uuid.UUID
    section_id: uuid.UUID | None = None
    author_id: uuid.UUID
    author_name: str | None = None
    content: str
    parent_id: uuid.UUID | None = None

    # Inline anchor fields
    quoted_text: str | None = None
    anchor_offset: int | None = None
    anchor_length: int | None = None

    # Resolution
    is_resolved: bool = False
    resolved_by: uuid.UUID | None = None
    resolved_by_name: str | None = None
    resolved_at: datetime | None = None

    # Threading: replies nested under this comment
    replies: list["CommentOut"] = []

    references: list[ReferenceOut] = []
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    section_id: uuid.UUID | None = None
    content: str
    parent_id: uuid.UUID | None = None
    quoted_text: str | None = None
    anchor_offset: int | None = None
    anchor_length: int | None = None
    references: list[ReferenceCreate] = []


class CommentUpdate(BaseModel):
    content: str | None = None
