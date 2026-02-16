"""Auth schemas for registration, login, and token responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.models.user import UserPlan


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User profile response."""

    id: uuid.UUID
    email: str
    full_name: str | None
    plan: UserPlan
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreateRequest(BaseModel):
    """Create API key request."""

    name: str = Field(min_length=1, max_length=200)


class ApiKeyResponse(BaseModel):
    """API key response (no secret shown)."""

    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(BaseModel):
    """Response when a new API key is created (includes full key, shown once)."""

    id: uuid.UUID
    name: str
    key_prefix: str
    full_key: str
    created_at: datetime

    model_config = {"from_attributes": True}
