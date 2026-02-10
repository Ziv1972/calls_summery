"""Tests for Pydantic schemas."""

import uuid
from datetime import datetime, timezone

from src.schemas.call import CallResponse, CallStatusResponse, CallUploadRequest
from src.schemas.common import ApiResponse, PaginatedResponse, StatusResponse
from src.schemas.summary import (
    CallDetailResponse,
    CallResponseMinimal,
    SummaryResponse,
    TranscriptionResponse,
)
from src.models.call import CallStatus, UploadSource
from src.models.summary import SummaryStatus


class TestCallSchemas:
    """Test call Pydantic schemas."""

    def test_call_response(self):
        now = datetime.now(timezone.utc)
        resp = CallResponse(
            id=uuid.uuid4(),
            filename="abc.mp3",
            original_filename="test.mp3",
            file_size_bytes=1024,
            content_type="audio/mpeg",
            upload_source=UploadSource.MANUAL,
            status=CallStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        assert resp.filename == "abc.mp3"
        assert resp.status == CallStatus.COMPLETED

    def test_call_status_response(self):
        resp = CallStatusResponse(
            call_id=uuid.uuid4(),
            status=CallStatus.TRANSCRIBING,
            transcription_status="processing",
        )
        assert resp.status == CallStatus.TRANSCRIBING
        assert resp.summary_status is None

    def test_call_upload_request_defaults(self):
        req = CallUploadRequest()
        assert req.language == "auto"
        assert req.upload_source == UploadSource.MANUAL

    def test_call_upload_request_custom(self):
        req = CallUploadRequest(language="he", upload_source=UploadSource.AUTO_AGENT)
        assert req.language == "he"


class TestCommonSchemas:
    """Test common Pydantic schemas."""

    def test_api_response_success(self):
        resp = ApiResponse(success=True, data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.error is None

    def test_api_response_error(self):
        resp = ApiResponse(success=False, error="Something went wrong")
        assert resp.success is False
        assert resp.data is None

    def test_paginated_response(self):
        resp = PaginatedResponse(
            items=["a", "b", "c"],
            total=10,
            page=1,
            page_size=3,
            total_pages=4,
        )
        assert len(resp.items) == 3
        assert resp.total_pages == 4

    def test_status_response(self):
        resp = StatusResponse(status="ok", message="Running")
        assert resp.status == "ok"


class TestSummarySchemas:
    """Test summary Pydantic schemas."""

    def test_summary_response(self):
        now = datetime.now(timezone.utc)
        resp = SummaryResponse(
            id=uuid.uuid4(),
            call_id=uuid.uuid4(),
            transcription_id=uuid.uuid4(),
            provider="claude",
            model="claude-haiku-4-5",
            summary_text="Test summary",
            key_points=["point1"],
            action_items=[],
            sentiment="positive",
            language="he",
            tokens_used=500,
            status=SummaryStatus.COMPLETED,
            created_at=now,
        )
        assert resp.summary_text == "Test summary"
        assert resp.status == SummaryStatus.COMPLETED

    def test_transcription_response(self):
        now = datetime.now(timezone.utc)
        resp = TranscriptionResponse(
            id=uuid.uuid4(),
            call_id=uuid.uuid4(),
            provider="deepgram",
            text="Hello",
            confidence=0.95,
            language="en",
            status="completed",
            created_at=now,
        )
        assert resp.provider == "deepgram"

    def test_call_response_minimal(self):
        now = datetime.now(timezone.utc)
        resp = CallResponseMinimal(
            id=uuid.uuid4(),
            filename="test.mp3",
            original_filename="test.mp3",
            status="completed",
            upload_source="manual",
            created_at=now,
        )
        assert resp.status == "completed"

    def test_call_detail_response(self):
        now = datetime.now(timezone.utc)
        call = CallResponseMinimal(
            id=uuid.uuid4(), filename="f", original_filename="f",
            status="completed", upload_source="manual", created_at=now,
        )
        detail = CallDetailResponse(call=call, transcription=None, summary=None)
        assert detail.call.status == "completed"
        assert detail.transcription is None
