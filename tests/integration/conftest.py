"""Integration test fixtures — shared app, mock session, mock user."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.deps import get_session
from src.api.main import create_app
from src.api.middleware.auth import get_current_user
from src.models.user import User, UserPlan


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.plan = UserPlan.FREE
    user.is_active = True
    user.is_verified = False
    user.created_at = MagicMock()
    return user


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def app(mock_user, mock_session):
    """Create FastAPI app with dependency overrides."""
    test_app = create_app()

    async def override_get_session():
        yield mock_session

    async def override_get_current_user():
        return mock_user

    test_app.dependency_overrides[get_session] = override_get_session
    test_app.dependency_overrides[get_current_user] = override_get_current_user

    yield test_app

    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Create async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
