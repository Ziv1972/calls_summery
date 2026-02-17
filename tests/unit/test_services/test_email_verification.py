"""Tests for email verification sending via EmailService."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.email_service import EmailResult, EmailService


class TestSendVerificationEmail:
    """Test EmailService.send_verification_email."""

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_send_verification_email_success(self, mock_sg_class, mock_settings):
        mock_settings.return_value.sendgrid_api_key = "test-key"
        mock_settings.return_value.sendgrid_from_email = "noreply@test.com"
        mock_settings.return_value.frontend_url = "http://localhost:8501"

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg-123"}
        mock_sg_class.return_value.send.return_value = mock_response

        svc = EmailService()
        result = svc.send_verification_email("user@example.com", "fake-token")

        assert result.success is True
        assert result.message_id == "msg-123"

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_send_verification_email_failure(self, mock_sg_class, mock_settings):
        mock_settings.return_value.sendgrid_api_key = "test-key"
        mock_settings.return_value.sendgrid_from_email = "noreply@test.com"
        mock_settings.return_value.frontend_url = "http://localhost:8501"

        mock_sg_class.return_value.send.side_effect = Exception("SendGrid down")

        svc = EmailService()
        result = svc.send_verification_email("user@example.com", "fake-token")

        assert result.success is False
        assert "SendGrid down" in result.error

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_verification_email_contains_url(self, mock_sg_class, mock_settings):
        mock_settings.return_value.sendgrid_api_key = "test-key"
        mock_settings.return_value.sendgrid_from_email = "noreply@test.com"
        mock_settings.return_value.frontend_url = "http://localhost:8501"

        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg-123"}
        mock_sg_class.return_value.send.return_value = mock_response

        svc = EmailService()
        svc.send_verification_email("user@example.com", "my-test-token")

        # Verify the send was called with HTML containing the verification URL
        call_args = mock_sg_class.return_value.send.call_args
        mail_obj = call_args[0][0]
        # Check the Content object's actual value
        content_value = mail_obj.contents[0].content
        assert "my-test-token" in content_value

    @patch("src.services.email_service.get_settings")
    @patch("src.services.email_service.SendGridAPIClient")
    def test_build_verification_html(self, mock_sg_class, mock_settings):
        mock_settings.return_value.sendgrid_api_key = "test-key"
        mock_settings.return_value.sendgrid_from_email = "noreply@test.com"

        svc = EmailService()
        html = svc._build_verification_html(verify_url="http://example.com/verify?token=abc")

        assert "http://example.com/verify?token=abc" in html
        assert "Verify Email" in html
        assert "24 hours" in html
