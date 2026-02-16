"""User model - represents a registered user."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base


class UserPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    plan: Mapped[UserPlan] = mapped_column(
        Enum(UserPlan), nullable=False, default=UserPlan.FREE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    calls: Mapped[list["Call"]] = relationship(  # noqa: F821
        back_populates="user", lazy="selectin"
    )
    settings: Mapped["UserSettings | None"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="selectin"
    )
