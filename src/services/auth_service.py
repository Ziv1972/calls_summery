"""Authentication service - JWT tokens and password hashing."""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.models.api_key import ApiKey
from src.models.user import User

ALGORITHM = "HS256"


@dataclass(frozen=True)
class TokenPair:
    """Immutable token pair result."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class TokenPayload:
    """Immutable decoded token payload."""

    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a JWT refresh token (7 days)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_token_pair(user_id: uuid.UUID) -> TokenPair:
    """Create access + refresh token pair."""
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    return TokenPayload(
        sub=payload["sub"],
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        type=payload["type"],
    )


def generate_api_key() -> tuple[str, str, str]:
    """Generate an API key. Returns (full_key, prefix, key_hash)."""
    prefix = "cs_" + secrets.token_hex(3)  # e.g. cs_a1b2c3
    secret_part = secrets.token_hex(24)
    full_key = f"{prefix}_{secret_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate user by email and password. Returns User or None."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def get_user_by_api_key(session: AsyncSession, api_key: str) -> User | None:
    """Look up user by API key. Returns User or None."""
    key_hash = hash_api_key(api_key)
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    api_key_record = result.scalar_one_or_none()
    if api_key_record is None:
        return None

    # Update last_used_at
    api_key_record.last_used_at = datetime.now(timezone.utc)
    await session.flush()

    return api_key_record.user
