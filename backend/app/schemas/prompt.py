import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromptVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    content: str
    change_summary: str
    changed_by_name: str | None = None
    created_at: datetime


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    content: str
    category: str
    model_key: str
    version: int
    is_active: bool
    updated_by_name: str | None = None
    created_at: datetime
    updated_at: datetime


class PromptDetailOut(PromptOut):
    versions: list[PromptVersionOut] = []


class PromptUpdate(BaseModel):
    content: str
    change_summary: str


class PromptTestRequest(BaseModel):
    content: str
    sample_input: str = "Tell me about a new authentication system for our microservices."


class PromptTestResponse(BaseModel):
    preview: str
    token_estimate: int
