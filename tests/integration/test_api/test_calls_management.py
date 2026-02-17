"""Integration tests for call reprocess and delete endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.call import CallStatus, UploadSource


def _make_call_mock(user_id, status=CallStatus.FAILED):
    """Create a mock Call object with all required fields."""
    call = MagicMock()
    call.id = uuid.uuid4()
    call.user_id = user_id
    call.s3_key = "calls/test.mp3"
    call.s3_bucket = "bucket"
    call.filename = "test.mp3"
    call.original_filename = "test.mp3"
    call.file_size_bytes = 1024
    call.content_type = "audio/mpeg"
    call.upload_source = UploadSource.MANUAL
    call.status = status
    call.duration_seconds = None
    call.language_detected = None
    call.error_message = "Transcription failed" if status == CallStatus.FAILED else None
    call.created_at = MagicMock()
    call.updated_at = MagicMock()
    return call


@pytest.mark.asyncio
class TestReprocessCall:
    """Test POST /api/calls/{id}/reprocess."""

    async def test_reprocess_failed_call_returns_200(self, client, mock_session, mock_user):
        call_mock = _make_call_mock(mock_user.id, CallStatus.FAILED)

        with (
            patch(
                "src.repositories.call_repository.CallRepository.find_by_id",
                side_effect=[call_mock, call_mock],
            ),
            patch(
                "src.repositories.call_repository.CallRepository.update",
                return_value=call_mock,
            ),
            patch("src.tasks.transcription_tasks.process_transcription.delay"),
            patch.object(mock_session, "execute", new_callable=AsyncMock),
            patch.object(mock_session, "commit", new_callable=AsyncMock),
        ):
            response = await client.post(f"/api/calls/{call_mock.id}/reprocess?language=he")
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_reprocess_non_failed_call_returns_400(self, client, mock_session, mock_user):
        call_mock = _make_call_mock(mock_user.id, CallStatus.COMPLETED)

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=call_mock,
        ):
            response = await client.post(f"/api/calls/{call_mock.id}/reprocess")
        assert response.status_code == 400

    async def test_reprocess_other_users_call_returns_404(self, client, mock_session, mock_user):
        call_mock = _make_call_mock(uuid.uuid4())  # different user

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=call_mock,
        ):
            response = await client.post(f"/api/calls/{call_mock.id}/reprocess")
        assert response.status_code == 404

    async def test_reprocess_nonexistent_call_returns_404(self, client, mock_session, mock_user):
        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=None,
        ):
            response = await client.post(f"/api/calls/{uuid.uuid4()}/reprocess")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteCall:
    """Test DELETE /api/calls/{id}."""

    async def test_delete_own_call_returns_200(self, client, mock_session, mock_user):
        call_mock = _make_call_mock(mock_user.id, CallStatus.COMPLETED)

        with (
            patch(
                "src.repositories.call_repository.CallRepository.find_by_id",
                return_value=call_mock,
            ),
            patch.object(mock_session, "execute", new_callable=AsyncMock),
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch.object(mock_session, "commit", new_callable=AsyncMock),
            patch("src.services.storage_service.StorageService.delete_file", return_value=True),
        ):
            response = await client.delete(f"/api/calls/{call_mock.id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_delete_other_users_call_returns_404(self, client, mock_session, mock_user):
        call_mock = _make_call_mock(uuid.uuid4())

        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=call_mock,
        ):
            response = await client.delete(f"/api/calls/{call_mock.id}")
        assert response.status_code == 404

    async def test_delete_nonexistent_call_returns_404(self, client, mock_session, mock_user):
        with patch(
            "src.repositories.call_repository.CallRepository.find_by_id",
            return_value=None,
        ):
            response = await client.delete(f"/api/calls/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_delete_s3_failure_still_returns_200(self, client, mock_session, mock_user):
        """S3 delete failure should not abort the DB deletion."""
        call_mock = _make_call_mock(mock_user.id, CallStatus.COMPLETED)

        with (
            patch(
                "src.repositories.call_repository.CallRepository.find_by_id",
                return_value=call_mock,
            ),
            patch.object(mock_session, "execute", new_callable=AsyncMock),
            patch.object(mock_session, "delete", new_callable=AsyncMock),
            patch.object(mock_session, "commit", new_callable=AsyncMock),
            patch(
                "src.services.storage_service.StorageService.delete_file",
                side_effect=Exception("S3 down"),
            ),
        ):
            response = await client.delete(f"/api/calls/{call_mock.id}")
        assert response.status_code == 200
