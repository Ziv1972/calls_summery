"""Upload API endpoints - presigned URLs for client-side S3 uploads."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.config.plan_limits import get_plan_limits
from src.config.settings import get_settings
from src.models.user import User
from src.repositories.call_repository import CallRepository
from src.schemas.common import ApiResponse
from src.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])


class PresignRequest(BaseModel):
    """Request for a presigned S3 upload URL."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)
    file_size_bytes: int = Field(..., gt=0)


class PresignResponse(BaseModel):
    """Presigned URL response for client-side upload."""

    upload_url: str
    s3_key: str
    s3_bucket: str
    expires_in: int


@router.post("/presign", response_model=ApiResponse[PresignResponse])
async def get_presigned_upload_url(
    body: PresignRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a presigned S3 PUT URL for client-side upload.

    Used by mobile apps that cannot embed AWS credentials.
    Validates content type, file size, and plan limits before issuing the URL.
    After uploading to S3, the client must call POST /api/webhooks/s3-upload
    to register the call and trigger the processing pipeline.
    """
    settings = get_settings()

    # Validate content type
    if body.content_type not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {body.content_type}. "
            f"Allowed: {settings.allowed_audio_formats}",
        )

    # Validate file size (hard ceiling)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if body.file_size_bytes > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB",
        )

    # Enforce plan limits
    limits = get_plan_limits(current_user.plan)
    plan_max_bytes = limits.max_file_size_mb * 1024 * 1024
    if body.file_size_bytes > plan_max_bytes:
        raise HTTPException(
            status_code=403,
            detail=f"File exceeds {limits.max_file_size_mb}MB limit for your {current_user.plan.value} plan",
        )

    if limits.calls_per_month is not None:
        call_repo = CallRepository(session)
        count = await call_repo.count_calls_this_month(current_user.id)
        if count >= limits.calls_per_month:
            raise HTTPException(
                status_code=403,
                detail=f"Monthly limit of {limits.calls_per_month} calls reached for {current_user.plan.value} plan",
            )

    # Generate presigned PUT URL
    storage = StorageService()
    result = storage.generate_presigned_put_url(
        original_filename=body.filename,
        content_type=body.content_type,
    )

    logger.info(
        "Presigned PUT URL generated for user %s: %s -> %s",
        current_user.id, body.filename, result.s3_key,
    )

    return ApiResponse(
        success=True,
        data=PresignResponse(
            upload_url=result.upload_url,
            s3_key=result.s3_key,
            s3_bucket=result.bucket,
            expires_in=result.expires_in,
        ),
    )
