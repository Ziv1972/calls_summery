"""Tests for settings API route helpers."""

from unittest.mock import MagicMock

import pytest

from src.api.routes.settings import SettingsResponse, SettingsUpdate


class TestSettingsSchemas:
    """Test settings request/response schemas."""

    def test_settings_response_defaults(self):
        """SettingsResponse should have sensible defaults."""
        response = SettingsResponse()
        assert response.summary_language == "auto"
        assert response.email_recipient is None
        assert response.notify_on_complete is True
        assert response.notification_method == "email"
        assert response.auto_upload_enabled is True

    def test_settings_response_with_values(self):
        """SettingsResponse should accept custom values."""
        response = SettingsResponse(
            summary_language="he",
            email_recipient="user@example.com",
            notify_on_complete=False,
            notification_method="both",
            auto_upload_enabled=False,
        )
        assert response.summary_language == "he"
        assert response.email_recipient == "user@example.com"
        assert response.notify_on_complete is False

    def test_settings_update_all_none(self):
        """SettingsUpdate with no fields should have all None."""
        update = SettingsUpdate()
        assert update.summary_language is None
        assert update.email_recipient is None
        assert update.notification_method is None

    def test_settings_update_partial(self):
        """SettingsUpdate should accept partial updates."""
        update = SettingsUpdate(
            email_recipient="new@example.com",
            notify_on_complete=True,
        )
        assert update.email_recipient == "new@example.com"
        assert update.notify_on_complete is True
        assert update.summary_language is None

    def test_settings_response_serialization(self):
        """SettingsResponse should serialize to dict."""
        response = SettingsResponse(
            summary_language="en",
            email_recipient="test@test.com",
        )
        data = response.model_dump()
        assert data["summary_language"] == "en"
        assert data["email_recipient"] == "test@test.com"
        assert isinstance(data, dict)
