"""Tests for email service."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.email_service import EmailResult, EmailService


class TestEmailService:
    """Test SendGrid email delivery."""

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_send_summary_success(self, mock_sg_cls, mock_settings):
        """Successful email send returns EmailResult with success=True."""
        mock_settings.return_value = MagicMock(
            sendgrid_api_key="test-key",
            sendgrid_from_email="test@example.com",
        )

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg-123"}

        mock_client = MagicMock()
        mock_client.send.return_value = mock_response
        mock_sg_cls.return_value = mock_client

        svc = EmailService()
        result = svc.send_summary(
            to_email="user@example.com",
            call_filename="meeting.mp3",
            summary_text="This is a test summary.",
            key_points=["Point 1", "Point 2"],
            action_items=["Action 1"],
        )

        assert isinstance(result, EmailResult)
        assert result.success is True
        assert result.message_id == "msg-123"
        assert result.error is None

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_send_summary_failure(self, mock_sg_cls, mock_settings):
        """Failed email send returns EmailResult with success=False."""
        mock_settings.return_value = MagicMock(
            sendgrid_api_key="test-key",
            sendgrid_from_email="test@example.com",
        )

        mock_client = MagicMock()
        mock_client.send.side_effect = Exception("API error")
        mock_sg_cls.return_value = mock_client

        svc = EmailService()
        result = svc.send_summary(
            to_email="user@example.com",
            call_filename="meeting.mp3",
            summary_text="Test summary.",
        )

        assert result.success is False
        assert "API error" in result.error

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_email_result_is_immutable(self, mock_sg_cls, mock_settings):
        """EmailResult should be frozen dataclass."""
        result = EmailResult(success=True, message_id="test-123")
        with pytest.raises(AttributeError):
            result.success = False

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_build_html_includes_key_points(self, mock_sg_cls, mock_settings):
        """HTML body should include key points and action items."""
        mock_settings.return_value = MagicMock(
            sendgrid_api_key="test-key",
            sendgrid_from_email="test@example.com",
        )

        svc = EmailService()
        html = svc._build_html(
            call_filename="test.mp3",
            summary_text="Summary text",
            key_points=["Point A", "Point B"],
            action_items=["Action X"],
        )

        assert "Point A" in html
        assert "Point B" in html
        assert "Action X" in html
        assert "test.mp3" in html

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_build_html_empty_lists(self, mock_sg_cls, mock_settings):
        """HTML body should handle empty key points and action items."""
        mock_settings.return_value = MagicMock(
            sendgrid_api_key="test-key",
            sendgrid_from_email="test@example.com",
        )

        svc = EmailService()
        html = svc._build_html(
            call_filename="test.mp3",
            summary_text="Summary text",
            key_points=[],
            action_items=[],
        )

        assert "Key Points" not in html
        assert "Action Items" not in html
        assert "Summary text" in html
