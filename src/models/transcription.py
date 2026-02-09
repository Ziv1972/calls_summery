"""Transcription model - represents transcription result."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base


class TranscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Transcription(Base):
    __tablename__ = "transcriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="deepgram"
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    speakers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    words_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[TranscriptionStatus] = mapped_column(
        Enum(TranscriptionStatus), nullable=False, default=TranscriptionStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    call: Mapped["Call"] = relationship(back_populates="transcription")  # noqa: F821
    summaries: Mapped[list["Summary"]] = relationship(  # noqa: F821
        back_populates="transcription", lazy="selectin"
    )
