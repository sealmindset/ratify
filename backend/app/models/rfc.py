import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RFCStatus(str, PyEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ARCHIVED = "archived"


class RFCType(str, PyEnum):
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PROCESS = "process"
    ARCHITECTURE = "architecture"
    INTEGRATION = "integration"
    DATA = "data"
    OTHER = "other"


class RFC(Base):
    __tablename__ = "rfcs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rfc_number: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    rfc_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    jira_epic_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    author = relationship("User", lazy="selectin")
    sections = relationship(
        "RFCSection", back_populates="rfc", lazy="selectin",
        cascade="all, delete-orphan", order_by="RFCSection.order"
    )
    comments = relationship(
        "Comment", back_populates="rfc", lazy="noload",
        cascade="all, delete-orphan"
    )
    review_assignments = relationship(
        "ReviewAssignment", back_populates="rfc", lazy="noload",
        cascade="all, delete-orphan"
    )
    sign_offs = relationship(
        "SignOff", back_populates="rfc", lazy="noload",
        cascade="all, delete-orphan"
    )
    ai_conversations = relationship(
        "AIConversation", back_populates="rfc", lazy="noload",
        cascade="all, delete-orphan"
    )
