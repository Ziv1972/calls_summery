"""Integration tests for plan gating on upload endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.call import CallStatus, UploadSource
from src.models.user import UserPlan


@pytest.mark.asyncio
class TestUploadPlanLimits:
    """Test plan limit enforcement on POST /api/calls/upload."""

    async def test_upload_blocked_when_monthly_limit_reached(self, client, mock_session, mock_user):
        """FREE plan user with 10 calls this month should be blocked."""
        mock_user.plan = UserPlan.FREE

        with (
            patch(
                "src.api.routes.calls.get_settings",
            ) as mock_settings,
            patch(
                "src.api.routes.calls.CallRepository",
            ) as mock_repo_cls,
        ):
            mock_settings.return_value.allowed_audio_formats = ["audio/wav"]
            mock_settings.return_value.max_upload_size_mb = 500
            mock_repo_cls.return_value.count_calls_this_month = AsyncMock(return_value=10)

            response = await client.post(
                "/api/calls/upload",
                files={"file": ("test.wav", b"\x00" * 100, "audio/wav")},
                data={"language": "auto"},
            )

        assert response.status_code == 403
        assert "Monthly limit" in response.json()["detail"]

    async def test_upload_blocked_when_file_too_large_for_plan(self, client, mock_session, mock_user):
        """FREE plan has 100MB limit."""
        mock_user.plan = UserPlan.FREE

        # Create content slightly over 100MB
        large_content = b"\x00" * (101 * 1024 * 1024)

        with patch(
            "src.api.routes.calls.get_settings",
        ) as mock_settings:
            mock_settings.return_value.allowed_audio_formats = ["audio/wav"]
            mock_settings.return_value.max_upload_size_mb = 500  # hard ceiling is higher

            response = await client.post(
                "/api/calls/upload",
                files={"file": ("test.wav", large_content, "audio/wav")},
                data={"language": "auto"},
            )

        assert response.status_code == 403
        assert "100MB limit" in response.json()["detail"]

    async def test_upload_allowed_under_limit(self, client, mock_session, mock_user):
        """FREE plan user with 5 calls should be allowed."""
        mock_user.plan = UserPlan.FREE

        call_mock = MagicMock()
        call_mock.id = uuid.uuid4()
        call_mock.filename = "test.wav"
        call_mock.original_filename = "test.wav"
        call_mock.file_size_bytes = 100
        call_mock.content_type = "audio/wav"
        call_mock.upload_source = UploadSource.MANUAL
        call_mock.status = CallStatus.UPLOADED
        call_mock.duration_seconds = None
        call_mock.language_detected = None
        call_mock.error_message = None
        call_mock.created_at = MagicMock()
        call_mock.updated_at = MagicMock()

        with (
            patch("src.api.routes.calls.get_settings") as mock_settings,
            patch("src.api.routes.calls.CallRepository") as mock_repo_cls,
            patch("src.api.routes.calls.CallService") as mock_svc_cls,
            patch("src.tasks.transcription_tasks.process_transcription") as mock_task,
        ):
            mock_settings.return_value.allowed_audio_formats = ["audio/wav"]
            mock_settings.return_value.max_upload_size_mb = 500
            mock_repo_cls.return_value.count_calls_this_month = AsyncMock(return_value=5)
            mock_svc_cls.return_value.upload_call = AsyncMock(return_value=call_mock.id)
            mock_repo_cls.return_value.find_by_id = AsyncMock(return_value=call_mock)

            response = await client.post(
                "/api/calls/upload",
                files={"file": ("test.wav", b"\x00" * 100, "audio/wav")},
                data={"language": "auto"},
            )

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_upload_business_unlimited(self, client, mock_session, mock_user):
        """BUSINESS plan should not be blocked by call count."""
        mock_user.plan = UserPlan.BUSINESS

        call_mock = MagicMock()
        call_mock.id = uuid.uuid4()
        call_mock.filename = "test.wav"
        call_mock.original_filename = "test.wav"
        call_mock.file_size_bytes = 100
        call_mock.content_type = "audio/wav"
        call_mock.upload_source = UploadSource.MANUAL
        call_mock.status = CallStatus.UPLOADED
        call_mock.duration_seconds = None
        call_mock.language_detected = None
        call_mock.error_message = None
        call_mock.created_at = MagicMock()
        call_mock.updated_at = MagicMock()

        with (
            patch("src.api.routes.calls.get_settings") as mock_settings,
            patch("src.api.routes.calls.CallRepository") as mock_repo_cls,
            patch("src.api.routes.calls.CallService") as mock_svc_cls,
            patch("src.tasks.transcription_tasks.process_transcription") as mock_task,
        ):
            mock_settings.return_value.allowed_audio_formats = ["audio/wav"]
            mock_settings.return_value.max_upload_size_mb = 500
            # count_calls_this_month should not even be called for BUSINESS
            mock_svc_cls.return_value.upload_call = AsyncMock(return_value=call_mock.id)
            mock_repo_cls.return_value.find_by_id = AsyncMock(return_value=call_mock)

            response = await client.post(
                "/api/calls/upload",
                files={"file": ("test.wav", b"\x00" * 100, "audio/wav")},
                data={"language": "auto"},
            )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestUpgradePlan:
    """Test POST /api/auth/upgrade-plan."""

    async def test_upgrade_plan_success(self, client, mock_session, mock_user):
        mock_user.plan = UserPlan.FREE
        mock_session.commit = AsyncMock()

        async def fake_refresh(obj):
            obj.plan = UserPlan.PRO

        mock_session.refresh = fake_refresh

        response = await client.post("/api/auth/upgrade-plan", json={
            "plan": "pro",
        })

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_upgrade_plan_invalid_plan(self, client, mock_session, mock_user):
        response = await client.post("/api/auth/upgrade-plan", json={
            "plan": "invalid",
        })

        assert response.status_code == 422


@pytest.mark.asyncio
class TestUsage:
    """Test GET /api/auth/usage."""

    async def test_get_usage_returns_plan_info(self, client, mock_session, mock_user):
        mock_user.plan = UserPlan.FREE

        with patch(
            "src.repositories.call_repository.CallRepository.count_calls_this_month",
            new_callable=AsyncMock,
            return_value=3,
        ):
            response = await client.get("/api/auth/usage")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["plan"] == "free"
        assert data["calls_this_month"] == 3
        assert data["calls_limit"] == 10
        assert data["max_file_size_mb"] == 100
