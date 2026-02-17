"""Integration tests for settings API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from src.models.settings import NotificationMethod, UserSettings


@pytest.mark.asyncio
class TestGetSettings:
    """Test GET /api/settings."""

    async def test_returns_default_settings_when_none_exist(self, client, mock_session):
        """When no settings exist, auto-creates defaults."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # After creating, flush + refresh populate defaults
        async def mock_refresh(obj):
            obj.summary_language = "auto"
            obj.email_recipient = None
            obj.whatsapp_recipient = None
            obj.notify_on_complete = True
            obj.notification_method = NotificationMethod.EMAIL
            obj.auto_upload_enabled = True

        mock_session.refresh = mock_refresh

        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["notification_method"] == "email"

    async def test_returns_existing_settings(self, client, mock_session, mock_user):
        """Returns existing user settings."""
        settings = MagicMock()
        settings.summary_language = "he"
        settings.email_recipient = "user@example.com"
        settings.whatsapp_recipient = "+972501234567"
        settings.notify_on_complete = True
        settings.notification_method = NotificationMethod.BOTH
        settings.auto_upload_enabled = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["summary_language"] == "he"
        assert data["whatsapp_recipient"] == "+972501234567"
        assert data["notification_method"] == "both"
        assert data["auto_upload_enabled"] is False


@pytest.mark.asyncio
class TestUpdateSettings:
    """Test PUT /api/settings."""

    async def test_update_notification_method(self, client, mock_session):
        """Update notification method to WhatsApp."""
        settings = MagicMock()
        settings.summary_language = "auto"
        settings.email_recipient = None
        settings.whatsapp_recipient = "+972501234567"
        settings.notify_on_complete = True
        settings.notification_method = NotificationMethod.EMAIL
        settings.auto_upload_enabled = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.notification_method = NotificationMethod.WHATSAPP

        mock_session.refresh = mock_refresh

        response = await client.put(
            "/api/settings",
            json={"notification_method": "whatsapp"},
        )
        assert response.status_code == 200
        assert settings.notification_method == NotificationMethod.WHATSAPP

    async def test_invalid_phone_rejected(self, client, mock_session):
        """Invalid WhatsApp number is rejected with 422."""
        response = await client.put(
            "/api/settings",
            json={"whatsapp_recipient": "not-a-phone"},
        )
        assert response.status_code == 422

    async def test_invalid_email_rejected(self, client, mock_session):
        """Invalid email is rejected with 422."""
        response = await client.put(
            "/api/settings",
            json={"email_recipient": "bad-email"},
        )
        assert response.status_code == 422

    async def test_invalid_method_rejected(self, client, mock_session):
        """Invalid notification method is rejected with 422."""
        response = await client.put(
            "/api/settings",
            json={"notification_method": "pigeon"},
        )
        assert response.status_code == 422

    async def test_invalid_language_rejected(self, client, mock_session):
        """Invalid language code is rejected with 422."""
        response = await client.put(
            "/api/settings",
            json={"summary_language": "klingon"},
        )
        assert response.status_code == 422

    async def test_valid_whatsapp_number_accepted(self, client, mock_session):
        """Valid WhatsApp number is accepted."""
        settings = MagicMock()
        settings.summary_language = "auto"
        settings.email_recipient = None
        settings.whatsapp_recipient = None
        settings.notify_on_complete = True
        settings.notification_method = NotificationMethod.EMAIL
        settings.auto_upload_enabled = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        async def mock_refresh(obj):
            pass

        mock_session.refresh = mock_refresh

        response = await client.put(
            "/api/settings",
            json={"whatsapp_recipient": "+972501234567"},
        )
        assert response.status_code == 200
        assert settings.whatsapp_recipient == "+972501234567"
