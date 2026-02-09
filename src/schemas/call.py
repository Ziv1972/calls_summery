"""Call schemas for API requests and responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.models.call import CallStatus, UploadSource


class CallResponse(BaseModel):
    """Call response schema."""

    id: uuid.UUID
    filename: str
    original_filename: str
    file_size_bytes: int
    duration_seconds: float | None = None
    content_type: str
    upload_source: UploadSource
    status: CallStatus
    language_detected: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CallStatusResponse(BaseModel):
    """Call processing status response."""

    call_id: uuid.UUID
    status: CallStatus
    transcription_status: str | None = None
    summary_status: str | None = None
    error_message: str | None = None


class CallUploadRequest(BaseModel):
    """Optional metadata for call upload."""

    language: str = Field(default="auto", description="Language code or 'auto' for detection")
    upload_source: UploadSource = UploadSource.MANUAL
