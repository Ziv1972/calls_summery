"""Summary schemas for API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from src.models.summary import SummaryStatus


class SummaryResponse(BaseModel):
    """Summary response schema."""

    id: uuid.UUID
    call_id: uuid.UUID
    transcription_id: uuid.UUID
    provider: str
    model: str
    summary_text: str | None = None
    key_points: list[str] | None = None
    action_items: list[str] | None = None
    sentiment: str | None = None
    language: str | None = None
    tokens_used: int | None = None
    status: SummaryStatus
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TranscriptionResponse(BaseModel):
    """Transcription response schema."""

    id: uuid.UUID
    call_id: uuid.UUID
    provider: str
    text: str | None = None
    confidence: float | None = None
    language: str | None = None
    duration_seconds: float | None = None
    speakers: dict | None = None
    words_count: int | None = None
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class CallDetailResponse(BaseModel):
    """Full call detail with transcription and summary."""

    call: "CallResponseMinimal"
    transcription: TranscriptionResponse | None = None
    summary: SummaryResponse | None = None


class CallResponseMinimal(BaseModel):
    """Minimal call info for nested responses."""

    id: uuid.UUID
    filename: str
    original_filename: str
    status: str
    upload_source: str
    language_detected: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
