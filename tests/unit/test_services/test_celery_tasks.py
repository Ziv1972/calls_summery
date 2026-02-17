"""Tests for Celery tasks (transcription, summarization, notification)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import uuid

import pytest


class TestProcessTranscription:
    """Test process_transcription Celery task."""

    @patch("src.config.settings.get_settings")
    def test_successful_transcription(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.transcription_tasks import process_transcription

        call_id = str(uuid.uuid4())
        call_mock = MagicMock()
        call_mock.s3_key = "calls/test.mp3"

        session_mock = MagicMock()
        session_mock.get.return_value = call_mock

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        mock_storage = MagicMock()
        mock_storage.generate_presigned_url.return_value = MagicMock(url="https://presigned")

        mock_transcription_svc = MagicMock()
        mock_transcription_svc.transcribe_sync.return_value = MagicMock(
            text="Hello", confidence=0.95, language="en",
            duration_seconds=30.0, external_id="req-1",
            words_count=1, speakers=[],
        )

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
            patch("src.services.storage_service.StorageService", return_value=mock_storage),
            patch("src.services.transcription_service.TranscriptionService", return_value=mock_transcription_svc),
            patch("src.tasks.summarization_tasks.process_summarization") as mock_summarization,
        ):
            task_mock = MagicMock()
            task_mock.retry = MagicMock(side_effect=Exception("retry"))
            process_transcription(call_id, "he")

            mock_transcription_svc.transcribe_sync.assert_called_once()

    @patch("src.config.settings.get_settings")
    def test_call_not_found(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.transcription_tasks import process_transcription

        session_mock = MagicMock()
        session_mock.get.return_value = None

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
        ):
            task_mock = MagicMock()
            result = process_transcription(str(uuid.uuid4()), "auto")
            assert result is None


class TestProcessSummarization:
    """Test process_summarization Celery task."""

    @patch("src.config.settings.get_settings")
    def test_successful_summarization(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.summarization_tasks import process_summarization

        call_id = str(uuid.uuid4())
        transcription_id = str(uuid.uuid4())

        call_mock = MagicMock()
        transcription_mock = MagicMock()
        transcription_mock.text = "Hello world"
        transcription_mock.language = "en"
        transcription_mock.speakers = [{"speaker": "Speaker 0", "text": "Hello"}]

        session_mock = MagicMock()
        session_mock.get.side_effect = [call_mock, transcription_mock]

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        mock_svc = MagicMock()
        mock_svc.summarize.return_value = MagicMock(
            summary_text="Summary", key_points=["p1"],
            action_items=[], sentiment="neutral",
            participants=[], tokens_used=100, model="haiku",
        )

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
            patch("src.services.summarization_service.SummarizationService", return_value=mock_svc),
            patch("src.tasks.notification_tasks.send_notifications"),
        ):
            task_mock = MagicMock()
            process_summarization(call_id, transcription_id, "he")
            mock_svc.summarize.assert_called_once()

    @patch("src.config.settings.get_settings")
    def test_call_or_transcription_not_found(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.summarization_tasks import process_summarization

        session_mock = MagicMock()
        session_mock.get.return_value = None

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
        ):
            task_mock = MagicMock()
            result = process_summarization(
                str(uuid.uuid4()), str(uuid.uuid4()), "auto"
            )
            assert result is None


class TestSendNotifications:
    """Test send_notifications Celery task."""

    @patch("src.config.settings.get_settings")
    def test_notifications_disabled(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.notification_tasks import send_notifications

        call_mock = MagicMock()
        call_mock.user_id = uuid.uuid4()
        summary_mock = MagicMock()

        user_settings_mock = MagicMock()
        user_settings_mock.notify_on_complete = False

        session_mock = MagicMock()
        session_mock.get.side_effect = [call_mock, summary_mock]
        session_mock.query.return_value.filter.return_value.first.return_value = user_settings_mock

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
        ):
            send_notifications(str(uuid.uuid4()), str(uuid.uuid4()))
            session_mock.commit.assert_not_called()

    @patch("src.config.settings.get_settings")
    def test_no_user_settings(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.tasks.notification_tasks import send_notifications

        call_mock = MagicMock()
        call_mock.user_id = uuid.uuid4()
        summary_mock = MagicMock()

        session_mock = MagicMock()
        session_mock.get.side_effect = [call_mock, summary_mock]
        session_mock.query.return_value.filter.return_value.first.return_value = None

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
        ):
            send_notifications(str(uuid.uuid4()), str(uuid.uuid4()))
            session_mock.commit.assert_not_called()

    @patch("src.config.settings.get_settings")
    def test_email_notification_sent(self, mock_get_settings):
        mock_get_settings.return_value = MagicMock(
            database_url="postgresql+asyncpg://localhost/test"
        )

        from src.models.settings import NotificationMethod
        from src.tasks.notification_tasks import send_notifications

        call_mock = MagicMock()
        call_mock.original_filename = "test.mp3"
        call_mock.id = uuid.uuid4()
        call_mock.user_id = uuid.uuid4()

        summary_mock = MagicMock()
        summary_mock.id = uuid.uuid4()
        summary_mock.summary_text = "Test summary"
        summary_mock.key_points = ["point"]
        summary_mock.action_items = []

        user_settings_mock = MagicMock()
        user_settings_mock.notify_on_complete = True
        user_settings_mock.notification_method = NotificationMethod.EMAIL
        user_settings_mock.email_recipient = "test@example.com"
        user_settings_mock.whatsapp_recipient = None

        session_mock = MagicMock()
        session_mock.get.side_effect = [call_mock, summary_mock]
        session_mock.query.return_value.filter.return_value.first.return_value = user_settings_mock

        session_ctx = MagicMock()
        session_ctx.__enter__ = MagicMock(return_value=session_mock)
        session_ctx.__exit__ = MagicMock(return_value=False)

        mock_email_svc = MagicMock()
        mock_email_svc.send_summary.return_value = MagicMock(
            success=True, message_id="msg-123", error=None
        )

        with (
            patch("sqlalchemy.create_engine"),
            patch("sqlalchemy.orm.Session", return_value=session_ctx),
            patch("src.services.email_service.EmailService", return_value=mock_email_svc),
        ):
            send_notifications(str(uuid.uuid4()), str(uuid.uuid4()))
            mock_email_svc.send_summary.assert_called_once()
            session_mock.commit.assert_called_once()
