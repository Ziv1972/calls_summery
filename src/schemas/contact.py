"""Contact schemas for API requests and responses."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _validate_phone_format(v: str) -> str:
    """Validate phone number contains only allowed characters and enough digits."""
    if not re.match(r'^[\d\s\-+()]+$', v):
        raise ValueError('Phone number may only contain digits, spaces, dashes, +, and parentheses')
    if len(re.sub(r'[^\d]', '', v)) < 7:
        raise ValueError('Phone number must contain at least 7 digits')
    return v


class ContactResponse(BaseModel):
    """Contact response schema."""

    id: uuid.UUID
    phone_number: str
    name: str | None = None
    company: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactCreateRequest(BaseModel):
    """Create a single contact."""

    phone_number: str = Field(min_length=3, max_length=20)
    name: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_phone_format(v)


class ContactUpdateRequest(BaseModel):
    """Update a contact."""

    name: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    notes: str | None = Field(default=None, max_length=2000)


class ContactSyncItem(BaseModel):
    """Single contact in a sync batch."""

    phone_number: str = Field(min_length=3, max_length=20)
    name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return _validate_phone_format(v)


class ContactSyncRequest(BaseModel):
    """Bulk sync contacts from mobile device."""

    contacts: list[ContactSyncItem] = Field(max_length=5000)
