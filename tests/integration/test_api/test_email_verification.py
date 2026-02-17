"""Integration tests for email verification endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.user import UserPlan


@pytest.mark.asyncio
class TestVerifyEmail:
    """Test POST /api/auth/verify-email."""

    async def test_verify_email_success(self, client, mock_session):
        user_mock = MagicMock()
        user_mock.id = uuid.uuid4()
        user_mock.email = "test@example.com"
        user_mock.full_name = "Test User"
        user_mock.plan = UserPlan.FREE
        user_mock.is_active = True
        user_mock.is_verified = False
        user_mock.created_at = MagicMock()

        mock_session.get = AsyncMock(return_value=user_mock)
        mock_session.commit = AsyncMock()

        async def fake_refresh(obj):
            obj.is_verified = True

        mock_session.refresh = fake_refresh

        with patch(
            "src.api.routes.auth.decode_token",
            return_value=MagicMock(sub=str(user_mock.id), type="email_verify"),
        ):
            response = await client.post("/api/auth/verify-email", json={
                "token": "valid-verification-token",
            })

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_verify_email_expired_token(self, client, mock_session):
        import jwt

        with patch(
            "src.api.routes.auth.decode_token",
            side_effect=jwt.ExpiredSignatureError("expired"),
        ):
            response = await client.post("/api/auth/verify-email", json={
                "token": "expired-token",
            })

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    async def test_verify_email_invalid_token(self, client, mock_session):
        import jwt

        with patch(
            "src.api.routes.auth.decode_token",
            side_effect=jwt.PyJWTError("invalid"),
        ):
            response = await client.post("/api/auth/verify-email", json={
                "token": "garbage",
            })

        assert response.status_code == 400

    async def test_verify_email_wrong_token_type(self, client, mock_session):
        with patch(
            "src.api.routes.auth.decode_token",
            return_value=MagicMock(sub=str(uuid.uuid4()), type="access"),
        ):
            response = await client.post("/api/auth/verify-email", json={
                "token": "access-token-not-verify",
            })

        assert response.status_code == 400
        assert "Invalid token type" in response.json()["detail"]

    async def test_verify_already_verified_user(self, client, mock_session):
        user_mock = MagicMock()
        user_mock.id = uuid.uuid4()
        user_mock.email = "test@example.com"
        user_mock.full_name = "Test User"
        user_mock.plan = UserPlan.FREE
        user_mock.is_active = True
        user_mock.is_verified = True
        user_mock.created_at = MagicMock()

        mock_session.get = AsyncMock(return_value=user_mock)

        with patch(
            "src.api.routes.auth.decode_token",
            return_value=MagicMock(sub=str(user_mock.id), type="email_verify"),
        ):
            response = await client.post("/api/auth/verify-email", json={
                "token": "valid-token",
            })

        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.asyncio
class TestResendVerification:
    """Test POST /api/auth/resend-verification."""

    async def test_resend_verification_success(self, client, mock_user):
        mock_user.is_verified = False

        with (
            patch(
                "src.api.routes.auth.create_email_verification_token",
                return_value="new-verify-token",
            ),
            patch(
                "src.services.email_service.EmailService",
            ) as mock_email_cls,
        ):
            mock_email_cls.return_value.send_verification_email.return_value = MagicMock(
                success=True, message_id="msg-456"
            )
            response = await client.post("/api/auth/resend-verification")

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "sent"

    async def test_resend_verification_already_verified(self, client, mock_user):
        mock_user.is_verified = True

        response = await client.post("/api/auth/resend-verification")

        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()

    async def test_resend_verification_email_failure(self, client, mock_user):
        mock_user.is_verified = False

        with (
            patch(
                "src.api.routes.auth.create_email_verification_token",
                return_value="new-verify-token",
            ),
            patch(
                "src.services.email_service.EmailService",
            ) as mock_email_cls,
        ):
            mock_email_cls.return_value.send_verification_email.return_value = MagicMock(
                success=False, error="SendGrid down"
            )
            response = await client.post("/api/auth/resend-verification")

        assert response.status_code == 500


@pytest.mark.asyncio
class TestRegisterSendsVerification:
    """Test that registration sends verification email."""

    async def test_register_sends_verification_email(self, client, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        async def fake_refresh(obj):
            obj.id = uuid.uuid4()
            obj.email = "new@example.com"
            obj.full_name = "New User"
            obj.plan = UserPlan.FREE
            obj.is_active = True
            obj.is_verified = False
            obj.created_at = MagicMock()

        mock_session.refresh = fake_refresh

        with (
            patch(
                "src.api.routes.auth.create_email_verification_token",
                return_value="verify-token",
            ) as mock_create_token,
            patch("src.services.email_service.EmailService") as mock_email_cls,
        ):
            response = await client.post("/api/auth/register", json={
                "email": "new@example.com",
                "password": "securepass123",
                "full_name": "New User",
            })

        assert response.status_code == 201
        mock_create_token.assert_called_once()
        mock_email_cls.return_value.send_verification_email.assert_called_once()
