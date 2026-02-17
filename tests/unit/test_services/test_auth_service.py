"""Tests for auth service - JWT tokens, password hashing, API key generation."""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import jwt
import pytest

from src.services.auth_service import (
    ALGORITHM,
    TokenPair,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self):
        result = hash_password("mysecretpassword")
        assert isinstance(result, str)
        assert result != "mysecretpassword"

    def test_verify_password_correct(self):
        hashed = hash_password("testpass123")
        assert verify_password("testpass123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("testpass123")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_unique_per_call(self):
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2  # bcrypt uses random salt

    def test_verify_both_hashes_work(self):
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert verify_password("samepassword", hash1) is True
        assert verify_password("samepassword", hash2) is True


class TestJWTTokens:
    """Test JWT token creation and decoding."""

    @patch("src.services.auth_service.get_settings")
    def test_create_access_token(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.access_token_expire_minutes = 60

        user_id = uuid.uuid4()
        token = create_access_token(user_id)

        assert isinstance(token, str)
        payload = jwt.decode(token, "test-secret-key-32chars-minimum!", algorithms=[ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    @patch("src.services.auth_service.get_settings")
    def test_create_refresh_token(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"

        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        payload = jwt.decode(token, "test-secret-key-32chars-minimum!", algorithms=[ALGORITHM])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    @patch("src.services.auth_service.get_settings")
    def test_create_token_pair(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.access_token_expire_minutes = 60

        user_id = uuid.uuid4()
        pair = create_token_pair(user_id)

        assert isinstance(pair, TokenPair)
        assert pair.token_type == "bearer"
        assert pair.access_token != pair.refresh_token

    @patch("src.services.auth_service.get_settings")
    def test_decode_access_token(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.access_token_expire_minutes = 60

        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == str(user_id)
        assert payload.type == "access"

    @patch("src.services.auth_service.get_settings")
    def test_decode_expired_token_raises(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"

        expired_payload = {
            "sub": str(uuid.uuid4()),
            "exp": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "type": "access",
        }
        token = jwt.encode(expired_payload, "test-secret-key-32chars-minimum!", algorithm=ALGORITHM)

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    @patch("src.services.auth_service.get_settings")
    def test_decode_invalid_token_raises(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"

        with pytest.raises(jwt.PyJWTError):
            decode_token("invalid.token.here")

    @patch("src.services.auth_service.get_settings")
    def test_decode_wrong_secret_raises(self, mock_settings):
        mock_settings.return_value.secret_key = "test-secret-key-32chars-minimum!"
        mock_settings.return_value.access_token_expire_minutes = 60

        token = create_access_token(uuid.uuid4())

        mock_settings.return_value.secret_key = "different-secret-key-32chars!!!!!"
        with pytest.raises(jwt.PyJWTError):
            decode_token(token)


class TestTokenPair:
    """Test TokenPair immutability."""

    def test_token_pair_is_frozen(self):
        pair = TokenPair(access_token="a", refresh_token="r")
        with pytest.raises(AttributeError):
            pair.access_token = "modified"


class TestTokenPayload:
    """Test TokenPayload immutability."""

    def test_token_payload_is_frozen(self):
        payload = TokenPayload(sub="123", exp=datetime.now(timezone.utc), type="access")
        with pytest.raises(AttributeError):
            payload.sub = "456"


class TestApiKeyGeneration:
    """Test API key generation and hashing."""

    def test_generate_api_key_format(self):
        full_key, prefix, key_hash = generate_api_key()

        assert full_key.startswith("cs_")
        assert prefix.startswith("cs_")
        assert full_key.startswith(prefix)
        assert len(key_hash) == 64  # SHA256 hex

    def test_generate_api_key_unique(self):
        key1, _, hash1 = generate_api_key()
        key2, _, hash2 = generate_api_key()

        assert key1 != key2
        assert hash1 != hash2

    def test_hash_api_key_deterministic(self):
        key = "cs_abc123_somesecretpart"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_hash_api_key_matches_generate(self):
        full_key, _, expected_hash = generate_api_key()
        actual_hash = hash_api_key(full_key)

        assert actual_hash == expected_hash


class TestUserModel:
    """Test User model enums."""

    def test_user_plan_values(self):
        from src.models.user import UserPlan

        assert UserPlan.FREE == "free"
        assert UserPlan.PRO == "pro"
        assert UserPlan.BUSINESS == "business"


class TestAuthSchemas:
    """Test auth Pydantic schemas."""

    def test_register_request_validation(self):
        from src.schemas.auth import RegisterRequest

        req = RegisterRequest(email="test@example.com", password="12345678")
        assert req.email == "test@example.com"

    def test_register_request_short_password(self):
        from src.schemas.auth import RegisterRequest

        with pytest.raises(Exception):  # ValidationError
            RegisterRequest(email="test@example.com", password="123")

    def test_register_request_invalid_email(self):
        from src.schemas.auth import RegisterRequest

        with pytest.raises(Exception):
            RegisterRequest(email="not-an-email", password="12345678")

    def test_login_request(self):
        from src.schemas.auth import LoginRequest

        req = LoginRequest(email="test@example.com", password="pass")
        assert req.email == "test@example.com"

    def test_token_response(self):
        from src.schemas.auth import TokenResponse

        resp = TokenResponse(access_token="a", refresh_token="r")
        assert resp.token_type == "bearer"

    def test_user_response_from_attributes(self):
        from src.schemas.auth import UserResponse

        assert UserResponse.model_config["from_attributes"] is True

    def test_api_key_create_request_validation(self):
        from src.schemas.auth import ApiKeyCreateRequest

        req = ApiKeyCreateRequest(name="My Key")
        assert req.name == "My Key"

    def test_api_key_create_request_empty_name(self):
        from src.schemas.auth import ApiKeyCreateRequest

        with pytest.raises(Exception):
            ApiKeyCreateRequest(name="")

    def test_verify_email_request(self):
        from src.schemas.auth import VerifyEmailRequest

        req = VerifyEmailRequest(token="some-jwt-token")
        assert req.token == "some-jwt-token"

    def test_upgrade_plan_request_valid(self):
        from src.schemas.auth import UpgradePlanRequest
        from src.models.user import UserPlan

        req = UpgradePlanRequest(plan="pro")
        assert req.plan == UserPlan.PRO

    def test_upgrade_plan_request_invalid(self):
        from src.schemas.auth import UpgradePlanRequest

        with pytest.raises(Exception):
            UpgradePlanRequest(plan="invalid")
