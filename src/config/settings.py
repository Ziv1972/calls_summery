"""Application settings loaded from environment variables."""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Calls Summary"
    debug: bool = False
    environment: str = Field(default="development")

    # Database - Railway provides DATABASE_URL in standard format
    database_url: str = "postgresql+asyncpg://postgres@localhost:5432/calls_summery"

    # Redis - Railway provides REDIS_URL
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver for SQLAlchemy async."""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "calls-summery"

    # Deepgram
    deepgram_api_key: str = ""

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-4-5-20251001"

    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@example.com"

    # Twilio (Phase 2)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None

    # Security
    secret_key: str = Field(default="change-this-to-a-random-string-at-least-32-chars")
    access_token_expire_minutes: int = 60

    # File Upload
    max_upload_size_mb: int = 500
    allowed_audio_formats: list[str] = [
        "audio/mpeg",
        "audio/mp4",
        "video/mp4",
        "audio/wav",
        "audio/x-m4a",
        "audio/ogg",
        "audio/webm",
        "audio/flac",
        "audio/x-flac",
    ]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ("development", "staging", "production")
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
