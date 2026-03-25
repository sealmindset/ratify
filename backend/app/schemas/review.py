import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_id: uuid.UUID
    section_id: uuid.UUID | None = None
    reviewer_id: uuid.UUID
    reviewer_name: str | None = None
    team: str
    status: str
    deadline: datetime | None = None
    jira_task_key: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewAssignmentCreate(BaseModel):
    section_id: uuid.UUID | None = None
    reviewer_id: uuid.UUID
    team: str
    deadline: datetime | None = None


class ReviewAssignmentUpdate(BaseModel):
    status: str | None = None
    deadline: datetime | None = None


class SignOffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rfc_id: uuid.UUID
    signer_id: uuid.UUID
    signer_name: str | None = None
    team: str
    status: str
    comment: str | None = None
    signed_at: datetime | None = None
    created_at: datetime


class SignOffCreate(BaseModel):
    signer_id: uuid.UUID
    team: str


class SignOffUpdate(BaseModel):
    status: str
    comment: str | None = None
