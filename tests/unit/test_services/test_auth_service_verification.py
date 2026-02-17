"""Tests for email verification token creation."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from src.services.auth_service import (
    ALGORITHM,
    create_email_verification_token,
    decode_token,
)


class TestEmailVerificationToken:
    """Test email verification token creation and decoding."""

    @patch("src.services.auth_service.get_settings")
    def test_token_has_email_verify_type(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.email_verification_expire_hours = 24

        user_id = uuid.uuid4()
        token = create_email_verification_token(user_id)

        payload = jwt.decode(token, "test-secret-key-32chars-minimum!", algorithms=[ALGORITHM])
        assert payload["type"] == "email_verify"
        assert payload["sub"] == str(user_id)

    @patch("src.services.auth_service.get_settings")
    def test_token_expiry_is_24_hours(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.email_verification_expire_hours = 24

        token = create_email_verification_token(uuid.uuid4())

        payload = jwt.decode(token, "test-secret-key-32chars-minimum!", algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = exp - now
        # Should be approximately 24 hours (within 1 minute tolerance)
        assert timedelta(hours=23, minutes=59) < diff < timedelta(hours=24, minutes=1)

    @patch("src.services.auth_service.get_settings")
    def test_token_is_string(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.email_verification_expire_hours = 24

        token = create_email_verification_token(uuid.uuid4())
        assert isinstance(token, str)

    @patch("src.services.auth_service.get_settings")
    def test_token_decodable_with_decode_token(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.email_verification_expire_hours = 24

        user_id = uuid.uuid4()
        token = create_email_verification_token(user_id)
        payload = decode_token(token)

        assert payload.type == "email_verify"
        assert payload.sub == str(user_id)

    @patch("src.services.auth_service.get_settings")
    def test_custom_expiry_hours(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.email_verification_expire_hours = 48

        token = create_email_verification_token(uuid.uuid4())

        payload = jwt.decode(token, "test-secret-key-32chars-minimum!", algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = exp - now
        assert timedelta(hours=47, minutes=59) < diff < timedelta(hours=48, minutes=1)
