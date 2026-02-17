"""Integration tests for calls API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.call import CallStatus, UploadSource


@pytest.mark.asyncio
class TestListCalls:
    """Test GET /api/calls."""

    async def test_list_calls_empty(self, client, mock_session, mock_user):
        """Returns empty list when no calls."""
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20
        mock_result.total_pages = 0

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_user",
            return_value=mock_result,
        ):
            response = await client.get("/api/calls/")
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0

    async def test_list_calls_with_pagination(self, client, mock_session, mock_user):
        """Returns paginated calls list."""
        call_mock = MagicMock()
        call_mock.id = uuid.uuid4()
        call_mock.filename = "test.mp3"
        call_mock.original_filename = "meeting.mp3"
        call_mock.s3_key = "calls/test.mp3"
        call_mock.s3_bucket = "bucket"
        call_mock.file_size_bytes = 1024
        call_mock.content_type = "audio/mpeg"
        call_mock.upload_source = UploadSource.MANUAL
        call_mock.status = CallStatus.COMPLETED
        call_mock.duration_seconds = 120.0
        call_mock.user_id = mock_user.id
        call_mock.language_detected = None
        call_mock.error_message = None
        call_mock.created_at = MagicMock()
        call_mock.updated_at = MagicMock()

        mock_result = MagicMock()
        mock_result.items = [call_mock]
        mock_result.total = 1
        mock_result.page = 1
        mock_result.page_size = 20
        mock_result.total_pages = 1

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_user",
            return_value=mock_result,
        ):
            response = await client.get("/api/calls/?page=1&page_size=20")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1


@pytest.mark.asyncio
class TestGetCall:
    """Test GET /api/calls/{call_id}."""

    async def test_get_call_not_found(self, client, mock_session, mock_user):
        """Returns 404 for nonexistent call."""
        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=None,
        ):
            call_id = uuid.uuid4()
            response = await client.get(f"/api/calls/{call_id}")
            assert response.status_code == 404

    async def test_get_call_wrong_user(self, client, mock_session, mock_user):
        """Returns 404 for call belonging to another user."""
        call_mock = MagicMock()
        call_mock.user_id = uuid.uuid4()  # Different user

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=call_mock,
        ):
            call_id = uuid.uuid4()
            response = await client.get(f"/api/calls/{call_id}")
            assert response.status_code == 404

    async def test_get_call_success(self, client, mock_session, mock_user):
        """Returns call details for own call."""
        call_id = uuid.uuid4()
        call_mock = MagicMock()
        call_mock.id = call_id
        call_mock.user_id = mock_user.id
        call_mock.filename = "test.mp3"
        call_mock.original_filename = "meeting.mp3"
        call_mock.s3_key = "calls/test.mp3"
        call_mock.s3_bucket = "bucket"
        call_mock.file_size_bytes = 1024
        call_mock.content_type = "audio/mpeg"
        call_mock.upload_source = UploadSource.MANUAL
        call_mock.status = CallStatus.COMPLETED
        call_mock.duration_seconds = 120.0
        call_mock.language_detected = None
        call_mock.error_message = None
        call_mock.created_at = MagicMock()
        call_mock.updated_at = MagicMock()

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=call_mock,
        ):
            response = await client.get(f"/api/calls/{call_id}")
            assert response.status_code == 200
            assert response.json()["success"] is True
