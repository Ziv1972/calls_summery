"""Tests for WhatsApp service."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.whatsapp_service import WhatsAppResult, WhatsAppService


class TestWhatsAppResult:
    """Test WhatsAppResult immutable dataclass."""

    def test_create_success_result(self):
        result = WhatsAppResult(success=True, message_sid="SM123")
        assert result.success is True
        assert result.message_sid == "SM123"
        assert result.error is None

    def test_create_failure_result(self):
        result = WhatsAppResult(success=False, error="Not configured")
        assert result.success is False
        assert result.error == "Not configured"

    def test_result_is_immutable(self):
        result = WhatsAppResult(success=True)
        with pytest.raises(AttributeError):
            result.success = False


class TestWhatsAppService:
    """Test WhatsAppService."""

    @patch("src.services.whatsapp_service.get_settings")
    def test_not_configured_returns_false(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number=None,
        )
        svc = WhatsAppService()
        assert svc.is_configured is False

    @patch("src.services.whatsapp_service.get_settings")
    def test_send_summary_when_not_configured(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number=None,
        )
        svc = WhatsAppService()
        result = svc.send_summary("+972501234567", "test.mp3", "Summary text")
        assert result.success is False
        assert "not configured" in result.error.lower()

    @patch("src.services.whatsapp_service.get_settings")
    def test_format_message_basic(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number=None,
        )
        svc = WhatsAppService()
        msg = svc._format_message("call.mp3", "Summary text", [], [])
        assert "call.mp3" in msg
        assert "Summary text" in msg

    @patch("src.services.whatsapp_service.get_settings")
    def test_format_message_with_key_points_and_actions(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number=None,
        )
        svc = WhatsAppService()
        msg = svc._format_message(
            "call.mp3", "Summary",
            key_points=["Point 1", "Point 2"],
            action_items=["Action 1"],
        )
        assert "Point 1" in msg
        assert "Point 2" in msg
        assert "Action 1" in msg

    @patch("src.services.whatsapp_service.get_settings")
    def test_format_message_truncation(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number=None,
        )
        svc = WhatsAppService()
        long_text = "x" * 2000
        msg = svc._format_message("call.mp3", long_text, [], [])
        assert len(msg) <= 1580
        assert msg.endswith("...")

    @patch("src.services.whatsapp_service.get_settings")
    def test_send_summary_success(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number="+14155238886",
        )

        mock_message = MagicMock()
        mock_message.sid = "SM_TEST_SID"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        svc = WhatsAppService()
        # Inject mock client directly (Twilio may not be installed)
        svc._client = mock_client
        svc._from_number = "+14155238886"

        result = svc.send_summary(
            to_number="+972501234567",
            call_filename="meeting.mp3",
            summary_text="Test summary",
            key_points=["Point 1"],
            action_items=["Action 1"],
        )

        assert result.success is True
        assert result.message_sid == "SM_TEST_SID"
        assert result.error is None

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["from_"] == "whatsapp:+14155238886"
        assert call_kwargs["to"] == "whatsapp:+972501234567"
        assert "meeting.mp3" in call_kwargs["body"]

    @patch("src.services.whatsapp_service.get_settings")
    def test_send_summary_twilio_error(self, mock_settings):
        mock_settings.return_value = MagicMock(
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_whatsapp_number="+14155238886",
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio API error: invalid number")

        svc = WhatsAppService()
        svc._client = mock_client
        svc._from_number = "+14155238886"

        result = svc.send_summary(
            to_number="+000000000",
            call_filename="test.mp3",
            summary_text="Summary",
        )

        assert result.success is False
        assert "Twilio API error" in result.error
        assert result.message_sid is None
