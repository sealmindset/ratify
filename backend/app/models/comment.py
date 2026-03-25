import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rfc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfcs.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rfc_sections.id", ondelete="CASCADE"), nullable=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )

    # Inline anchor fields -- ties comment to specific text in a section
    quoted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    anchor_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anchor_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Resolution tracking
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
    rfc = relationship("RFC", back_populates="comments")
    section = relationship("RFCSection", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id], lazy="selectin")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="selectin")
    parent = relationship("Comment", remote_side="Comment.id", lazy="noload")
    replies = relationship("Comment", lazy="noload", cascade="all, delete-orphan")
    references = relationship(
        "Reference", back_populates="comment", lazy="selectin",
        cascade="all, delete-orphan"
    )
