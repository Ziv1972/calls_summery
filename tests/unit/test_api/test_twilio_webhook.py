"""Tests for Twilio delivery status webhook."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.models.notification import NotificationStatus


@pytest.fixture
def mock_notification():
    """Create a mock notification with SENT status."""
    notification = MagicMock()
    notification.id = uuid.uuid4()
    notification.external_id = "SM1234567890"
    notification.status = NotificationStatus.SENT
    notification.error_message = None
    return notification


@pytest.fixture
def app():
    """Create test FastAPI app."""
    from src.api.main import create_app

    return create_app()


@pytest.mark.asyncio
class TestTwilioStatusCallback:
    """Test Twilio delivery status webhook endpoint."""

    async def test_delivery_status_delivered(self, app, mock_notification):
        """Test successful delivery status update."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        app.dependency_overrides[__import__("src.api.deps", fromlist=["get_session"]).get_session] = mock_get_session

        with patch("src.api.routes.webhooks.verify_twilio_signature", return_value=None):
            app.dependency_overrides[
                __import__("src.api.routes.webhooks", fromlist=["verify_twilio_signature"]).verify_twilio_signature
            ] = lambda: None

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/webhooks/twilio/status",
                    data={
                        "MessageSid": "SM1234567890",
                        "MessageStatus": "delivered",
                    },
                )

            assert response.status_code == 200
            assert response.json()["status"] == "updated"
            assert mock_notification.status == NotificationStatus.DELIVERED

        app.dependency_overrides.clear()

    async def test_delivery_status_failed_with_error_code(self, app, mock_notification):
        """Test failed delivery status with error code."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        from src.api.deps import get_session
        from src.api.routes.webhooks import verify_twilio_signature

        app.dependency_overrides[get_session] = mock_get_session
        app.dependency_overrides[verify_twilio_signature] = lambda: None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/twilio/status",
                data={
                    "MessageSid": "SM1234567890",
                    "MessageStatus": "failed",
                    "ErrorCode": "30008",
                },
            )

        assert response.status_code == 200
        assert mock_notification.status == NotificationStatus.FAILED
        assert "30008" in mock_notification.error_message

        app.dependency_overrides.clear()

    async def test_unknown_message_sid_returns_200(self, app):
        """Test that unknown SID still returns 200 (don't expose info)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        async def mock_get_session():
            yield mock_session

        from src.api.deps import get_session
        from src.api.routes.webhooks import verify_twilio_signature

        app.dependency_overrides[get_session] = mock_get_session
        app.dependency_overrides[verify_twilio_signature] = lambda: None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/twilio/status",
                data={
                    "MessageSid": "SM_UNKNOWN",
                    "MessageStatus": "delivered",
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "not_found"

        app.dependency_overrides.clear()

    async def test_empty_message_sid_ignored(self, app):
        """Test that empty MessageSid is ignored."""
        mock_session = AsyncMock()

        async def mock_get_session():
            yield mock_session

        from src.api.deps import get_session
        from src.api.routes.webhooks import verify_twilio_signature

        app.dependency_overrides[get_session] = mock_get_session
        app.dependency_overrides[verify_twilio_signature] = lambda: None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/twilio/status",
                data={"MessageSid": "", "MessageStatus": "delivered"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

        app.dependency_overrides.clear()
