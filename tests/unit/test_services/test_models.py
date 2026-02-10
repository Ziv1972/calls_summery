"""Tests for SQLAlchemy models (enums, defaults, relationships)."""

import uuid

from src.models.call import Call, CallStatus, UploadSource
from src.models.notification import DeliveryType, Notification, NotificationStatus
from src.models.settings import NotificationMethod, UserSettings
from src.models.summary import Summary, SummaryStatus
from src.models.transcription import Transcription, TranscriptionStatus


class TestCallModel:
    """Test Call model enums."""

    def test_call_status_values(self):
        assert CallStatus.UPLOADED == "uploaded"
        assert CallStatus.TRANSCRIBING == "transcribing"
        assert CallStatus.TRANSCRIBED == "transcribed"
        assert CallStatus.SUMMARIZING == "summarizing"
        assert CallStatus.COMPLETED == "completed"
        assert CallStatus.FAILED == "failed"

    def test_upload_source_values(self):
        assert UploadSource.MANUAL == "manual"
        assert UploadSource.AUTO_AGENT == "auto_agent"
        assert UploadSource.CLOUD_SYNC == "cloud_sync"


class TestTranscriptionModel:
    """Test Transcription model enums."""

    def test_transcription_status_values(self):
        assert TranscriptionStatus.PENDING == "pending"
        assert TranscriptionStatus.PROCESSING == "processing"
        assert TranscriptionStatus.COMPLETED == "completed"
        assert TranscriptionStatus.FAILED == "failed"


class TestSummaryModel:
    """Test Summary model enums."""

    def test_summary_status_values(self):
        assert SummaryStatus.PENDING == "pending"
        assert SummaryStatus.PROCESSING == "processing"
        assert SummaryStatus.COMPLETED == "completed"
        assert SummaryStatus.FAILED == "failed"


class TestNotificationModel:
    """Test Notification model enums."""

    def test_delivery_type_values(self):
        assert DeliveryType.EMAIL == "email"
        assert DeliveryType.WHATSAPP == "whatsapp"

    def test_notification_status_values(self):
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.DELIVERED == "delivered"


class TestSettingsModel:
    """Test UserSettings model enums."""

    def test_notification_method_values(self):
        assert NotificationMethod.EMAIL == "email"
        assert NotificationMethod.WHATSAPP == "whatsapp"
        assert NotificationMethod.BOTH == "both"
        assert NotificationMethod.NONE == "none"

    def test_notification_method_is_string_enum(self):
        assert isinstance(NotificationMethod.EMAIL, str)
        assert NotificationMethod.EMAIL == "email"


class TestPaginationResult:
    """Test PaginationResult dataclass."""

    def test_total_pages_calculation(self):
        from src.repositories.base import PaginationResult

        result = PaginationResult(items=[], total=25, page=1, page_size=10)
        assert result.total_pages == 3

    def test_total_pages_exact_division(self):
        from src.repositories.base import PaginationResult

        result = PaginationResult(items=[], total=20, page=1, page_size=10)
        assert result.total_pages == 2

    def test_total_pages_zero_total(self):
        from src.repositories.base import PaginationResult

        result = PaginationResult(items=[], total=0, page=1, page_size=10)
        assert result.total_pages == 1

    def test_total_pages_one_item(self):
        from src.repositories.base import PaginationResult

        result = PaginationResult(items=[], total=1, page=1, page_size=10)
        assert result.total_pages == 1
