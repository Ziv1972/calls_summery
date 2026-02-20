"""Summary model - represents Claude API summarization result."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base


class SummaryStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False
    )
    transcription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcriptions.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="claude")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    action_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    structured_actions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    participants_details: Mapped[list | None] = mapped_column(JSON, nullable=True)
    topics: Mapped[list | None] = mapped_column(JSON, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[SummaryStatus] = mapped_column(
        Enum(SummaryStatus), nullable=False, default=SummaryStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    call: Mapped["Call"] = relationship(back_populates="summaries")  # noqa: F821
    transcription: Mapped["Transcription"] = relationship(  # noqa: F821
        back_populates="summaries"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        back_populates="summary", lazy="selectin"
    )
