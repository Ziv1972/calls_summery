"""User settings model - preferences for language, notifications, auto-upload."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base


class NotificationMethod(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    BOTH = "both"
    NONE = "none"


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True, index=True
    )
    auto_upload_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    summary_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="auto"
    )
    email_recipient: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_recipient: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notify_on_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    notification_method: Mapped[NotificationMethod] = mapped_column(
        Enum(NotificationMethod), nullable=False, default=NotificationMethod.EMAIL
    )
    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="settings")  # noqa: F821

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
