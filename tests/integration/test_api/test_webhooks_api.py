"""Integration tests for webhook API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.routes.webhooks import verify_twilio_signature
from src.models.notification import NotificationStatus


@pytest.mark.asyncio
class TestS3UploadWebhook:
    """Test POST /api/webhooks/s3-upload."""

    async def test_s3_upload_triggers_processing(self, client, mock_session, mock_user):
        """S3 upload webhook creates call and triggers Celery task."""
        # No existing call with this key
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_call = MagicMock()
        mock_call.id = uuid.uuid4()

        with (
            patch("src.repositories.call_repository.CallRepository.find_by_s3_key", return_value=None),
            patch("src.repositories.call_repository.CallRepository.create", return_value=mock_call),
            patch("src.tasks.transcription_tasks.process_transcription") as mock_task,
        ):
            response = await client.post(
                "/api/webhooks/s3-upload",
                json={
                    "bucket": "test-bucket",
                    "key": "calls/test-file.mp3",
                    "size": 1024000,
                    "content_type": "audio/mpeg",
                    "original_filename": "meeting.mp3",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "call_id" in data

    async def test_s3_upload_with_mobile_source(self, client, mock_session, mock_user):
        """S3 upload webhook accepts upload_source from payload."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_call = MagicMock()
        mock_call.id = uuid.uuid4()

        with (
            patch("src.repositories.call_repository.CallRepository.find_by_s3_key", return_value=None),
            patch("src.repositories.call_repository.CallRepository.create", return_value=mock_call) as mock_create,
            patch("src.tasks.transcription_tasks.process_transcription"),
        ):
            response = await client.post(
                "/api/webhooks/s3-upload",
                json={
                    "bucket": "test-bucket",
                    "key": "calls/mobile-file.m4a",
                    "size": 500000,
                    "content_type": "audio/x-m4a",
                    "original_filename": "call_recording.m4a",
                    "upload_source": "mobile_auto",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "processing"
        create_args = mock_create.call_args[0][0]
        assert create_args["upload_source"].value == "mobile_auto"

    async def test_s3_upload_with_invalid_source_falls_back(self, client, mock_session, mock_user):
        """Invalid upload_source falls back to auto_agent."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_call = MagicMock()
        mock_call.id = uuid.uuid4()

        with (
            patch("src.repositories.call_repository.CallRepository.find_by_s3_key", return_value=None),
            patch("src.repositories.call_repository.CallRepository.create", return_value=mock_call) as mock_create,
            patch("src.tasks.transcription_tasks.process_transcription"),
        ):
            response = await client.post(
                "/api/webhooks/s3-upload",
                json={
                    "bucket": "test-bucket",
                    "key": "calls/test.mp3",
                    "size": 1000,
                    "upload_source": "invalid_source",
                },
            )

        assert response.status_code == 200
        create_args = mock_create.call_args[0][0]
        assert create_args["upload_source"].value == "auto_agent"

    async def test_duplicate_s3_key_returns_already_exists(self, client, mock_session):
        """Duplicate S3 key returns already_exists."""
        existing_call = MagicMock()
        existing_call.id = uuid.uuid4()

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_s3_key",
            return_value=existing_call,
        ):
            response = await client.post(
                "/api/webhooks/s3-upload",
                json={
                    "bucket": "test-bucket",
                    "key": "calls/existing.mp3",
                    "size": 1024000,
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "already_exists"


@pytest.mark.asyncio
class TestTwilioStatusWebhook:
    """Test POST /api/webhooks/twilio/status."""

    @pytest.fixture
    def app_with_twilio_bypass(self, app):
        """Override Twilio signature verification."""
        app.dependency_overrides[verify_twilio_signature] = lambda: None
        yield app
        # cleared by the parent app fixture

    async def test_delivered_updates_notification(self, client, mock_session, app_with_twilio_bypass):
        """Delivered status updates notification to DELIVERED."""
        notification = MagicMock()
        notification.id = uuid.uuid4()
        notification.status = NotificationStatus.SENT
        notification.error_message = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_session.execute.return_value = mock_result

        response = await client.post(
            "/api/webhooks/twilio/status",
            data={"MessageSid": "SM_TEST", "MessageStatus": "delivered"},
        )

        assert response.status_code == 200
        assert notification.status == NotificationStatus.DELIVERED

    async def test_failed_updates_with_error_code(self, client, mock_session, app_with_twilio_bypass):
        """Failed status captures error code."""
        notification = MagicMock()
        notification.id = uuid.uuid4()
        notification.status = NotificationStatus.SENT
        notification.error_message = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_session.execute.return_value = mock_result

        response = await client.post(
            "/api/webhooks/twilio/status",
            data={
                "MessageSid": "SM_TEST",
                "MessageStatus": "failed",
                "ErrorCode": "30008",
            },
        )

        assert response.status_code == 200
        assert notification.status == NotificationStatus.FAILED
        assert "30008" in notification.error_message

    async def test_unknown_sid_returns_not_found(self, client, mock_session, app_with_twilio_bypass):
        """Unknown SID returns not_found (but 200 status)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = await client.post(
            "/api/webhooks/twilio/status",
            data={"MessageSid": "SM_UNKNOWN", "MessageStatus": "delivered"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "not_found"
