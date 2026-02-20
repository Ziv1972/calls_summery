"""Call model - represents an uploaded phone call recording."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base


class CallStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadSource(str, enum.Enum):
    MANUAL = "manual"
    AUTO_AGENT = "auto_agent"
    CLOUD_SYNC = "cloud_sync"
    MOBILE_AUTO = "mobile_auto"
    MOBILE_MANUAL = "mobile_manual"


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    caller_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    upload_source: Mapped[UploadSource] = mapped_column(
        Enum(UploadSource), nullable=False, default=UploadSource.MANUAL
    )
    status: Mapped[CallStatus] = mapped_column(
        Enum(CallStatus), nullable=False, default=CallStatus.UPLOADED
    )
    language_detected: Mapped[str | None] = mapped_column(String(10), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="calls")  # noqa: F821
    contact: Mapped["Contact | None"] = relationship(back_populates="calls")  # noqa: F821
    transcription: Mapped["Transcription"] = relationship(  # noqa: F821
        back_populates="call", uselist=False, lazy="selectin"
    )
    summaries: Mapped[list["Summary"]] = relationship(  # noqa: F821
        back_populates="call", lazy="selectin"
    )
