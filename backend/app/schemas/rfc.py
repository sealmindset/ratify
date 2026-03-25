import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RFCSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_id: uuid.UUID
    title: str
    content: str | None = None
    section_type: str
    order: int
    created_at: datetime
    updated_at: datetime


class RFCSectionCreate(BaseModel):
    title: str
    content: str | None = None
    section_type: str = "body"
    order: int = 0


class RFCSectionUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    section_type: str | None = None
    order: int | None = None


class RFCOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_number: int
    title: str
    summary: str | None = None
    rfc_type: str
    status: str
    author_id: uuid.UUID
    author_name: str | None = None
    jira_epic_key: str | None = None
    sections: list[RFCSectionOut] = []
    created_at: datetime
    updated_at: datetime


class RFCListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_number: int
    title: str
    summary: str | None = None
    rfc_type: str
    status: str
    author_id: uuid.UUID
    author_name: str | None = None
    jira_epic_key: str | None = None
    comment_count: int = 0
    review_count: int = 0
    created_at: datetime
    updated_at: datetime


class RFCCreate(BaseModel):
    title: str
    summary: str | None = None
    rfc_type: str = "other"


class RFCUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    rfc_type: str | None = None
    status: str | None = None
