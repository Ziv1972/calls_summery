"""Integration tests for auth endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.user import UserPlan


@pytest.mark.asyncio
class TestRegister:
    """Test POST /api/auth/register."""

    async def test_register_success(self, client, mock_session):
        # No existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        # After refresh, the user object needs proper attributes
        user_mock = MagicMock()
        user_mock.id = uuid.uuid4()
        user_mock.email = "new@example.com"
        user_mock.full_name = "New User"
        user_mock.plan = UserPlan.FREE
        user_mock.is_active = True
        user_mock.is_verified = False
        user_mock.created_at = MagicMock()

        async def fake_refresh(obj):
            # Copy attributes from user_mock to the actual user object
            obj.id = user_mock.id
            obj.email = "new@example.com"
            obj.full_name = "New User"
            obj.plan = UserPlan.FREE
            obj.is_active = True
            obj.is_verified = False
            obj.created_at = user_mock.created_at

        mock_session.refresh = fake_refresh

        response = await client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "securepass123",
            "full_name": "New User",
        })
        assert response.status_code == 201
        assert response.json()["success"] is True

    async def test_register_duplicate_email_returns_409(self, client, mock_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = await client.post("/api/auth/register", json={
            "email": "existing@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 409

    async def test_register_short_password_returns_422(self, client):
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "short",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Test POST /api/auth/login."""

    async def test_login_success_returns_tokens(self, client, mock_session, mock_user):
        with (
            patch(
                "src.api.routes.auth.authenticate_user",
                new_callable=AsyncMock,
                return_value=mock_user,
            ),
            patch(
                "src.api.routes.auth.create_token_pair",
                return_value=MagicMock(access_token="acc", refresh_token="ref"),
            ),
        ):
            response = await client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123",
            })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"] == "acc"
        assert data["data"]["refresh_token"] == "ref"

    async def test_login_invalid_credentials_returns_401(self, client, mock_session):
        with patch(
            "src.api.routes.auth.authenticate_user",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrong",
            })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetMe:
    """Test GET /api/auth/me."""

    async def test_get_me_returns_user_profile(self, client, mock_user):
        response = await client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == mock_user.email
