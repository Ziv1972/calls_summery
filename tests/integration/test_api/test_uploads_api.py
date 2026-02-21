"""Integration tests for upload presign API endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.user import UserPlan
from src.services.storage_service import PresignedPutResult


@pytest.mark.asyncio
class TestPresignEndpoint:
    """Test POST /api/uploads/presign."""

    async def test_presign_success(self, client, mock_user):
        """Valid request returns presigned PUT URL."""
        mock_result = PresignedPutResult(
            upload_url="https://s3.amazonaws.com/presigned-put",
            s3_key="calls/uuid.m4a",
            bucket="test-bucket",
            expires_in=900,
        )

        with (
            patch("src.api.routes.uploads.CallRepository") as mock_repo_cls,
            patch("src.api.routes.uploads.StorageService") as mock_storage_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.count_calls_this_month = AsyncMock(return_value=0)
            mock_repo_cls.return_value = mock_repo

            mock_storage = MagicMock()
            mock_storage.generate_presigned_put_url.return_value = mock_result
            mock_storage_cls.return_value = mock_storage

            response = await client.post(
                "/api/uploads/presign",
                json={
                    "filename": "test.m4a",
                    "content_type": "audio/x-m4a",
                    "file_size_bytes": 100000,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["upload_url"] == "https://s3.amazonaws.com/presigned-put"
        assert data["data"]["s3_key"] == "calls/uuid.m4a"
        assert data["data"]["s3_bucket"] == "test-bucket"
        assert data["data"]["expires_in"] == 900

    async def test_presign_unsupported_format(self, client):
        """Unsupported audio format returns 400."""
        response = await client.post(
            "/api/uploads/presign",
            json={
                "filename": "test.txt",
                "content_type": "text/plain",
                "file_size_bytes": 100,
            },
        )

        assert response.status_code == 400
        assert "Unsupported audio format" in response.json()["detail"]

    async def test_presign_file_too_large(self, client):
        """File exceeding hard ceiling returns 400."""
        response = await client.post(
            "/api/uploads/presign",
            json={
                "filename": "big.mp3",
                "content_type": "audio/mpeg",
                "file_size_bytes": 600 * 1024 * 1024,  # 600MB > 500MB limit
            },
        )

        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    async def test_presign_plan_limit_file_size(self, client, mock_user):
        """File exceeding plan limit returns 403."""
        mock_user.plan = UserPlan.FREE  # 100MB limit

        response = await client.post(
            "/api/uploads/presign",
            json={
                "filename": "big.mp3",
                "content_type": "audio/mpeg",
                "file_size_bytes": 150 * 1024 * 1024,  # 150MB > 100MB free limit
            },
        )

        assert response.status_code == 403
        assert "limit" in response.json()["detail"].lower()

    async def test_presign_monthly_limit_reached(self, client, mock_user):
        """Monthly call limit reached returns 403."""
        mock_user.plan = UserPlan.FREE  # 10 calls/month

        with patch("src.api.routes.uploads.CallRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.count_calls_this_month = AsyncMock(return_value=10)
            mock_repo_cls.return_value = mock_repo

            response = await client.post(
                "/api/uploads/presign",
                json={
                    "filename": "test.mp3",
                    "content_type": "audio/mpeg",
                    "file_size_bytes": 1000,
                },
            )

        assert response.status_code == 403
        assert "Monthly limit" in response.json()["detail"]

    async def test_presign_missing_filename(self, client):
        """Missing filename returns 422."""
        response = await client.post(
            "/api/uploads/presign",
            json={
                "content_type": "audio/mpeg",
                "file_size_bytes": 1000,
            },
        )

        assert response.status_code == 422

    async def test_presign_zero_file_size(self, client):
        """Zero file size returns 422."""
        response = await client.post(
            "/api/uploads/presign",
            json={
                "filename": "test.mp3",
                "content_type": "audio/mpeg",
                "file_size_bytes": 0,
            },
        )

        assert response.status_code == 422
