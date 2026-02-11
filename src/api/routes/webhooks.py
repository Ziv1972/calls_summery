"""Webhook endpoints for S3 events and external callbacks."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class S3EventPayload(BaseModel):
    """S3 event notification payload (simplified)."""

    bucket: str
    key: str
    size: int
    content_type: str = "audio/mpeg"
    original_filename: str | None = None


@router.post("/s3-upload")
async def s3_upload_event(
    payload: S3EventPayload,
    session: AsyncSession = Depends(get_session),
):
    """Handle S3 upload event from local agent or S3 notifications.

    When the local agent uploads a file to S3, it calls this webhook
    to trigger the processing pipeline.
    """
    from src.models.call import CallStatus, UploadSource
    from src.repositories.call_repository import CallRepository

    call_repo = CallRepository(session)

    # Check if already processed
    existing = await call_repo.find_by_s3_key(payload.key)
    if existing is not None:
        logger.info("S3 key %s already registered, skipping", payload.key)
        return {"status": "already_exists", "call_id": str(existing.id)}

    # Create call record
    filename = payload.key.split("/")[-1]
    original = payload.original_filename or filename
    call = await call_repo.create({
        "filename": filename,
        "original_filename": original,
        "s3_key": payload.key,
        "s3_bucket": payload.bucket,
        "file_size_bytes": payload.size,
        "content_type": payload.content_type,
        "upload_source": UploadSource.AUTO_AGENT,
        "status": CallStatus.UPLOADED,
    })
    await session.commit()

    # Read language preference from user settings
    from sqlalchemy import select
    from src.models.settings import UserSettings

    result = await session.execute(select(UserSettings).limit(1))
    user_settings = result.scalar_one_or_none()
    language = user_settings.summary_language if user_settings else "he"

    # Trigger processing
    from src.tasks.transcription_tasks import process_transcription

    process_transcription.delay(str(call.id), language)

    logger.info("Auto-upload registered: %s (call_id=%s)", payload.key, call.id)
    return {"status": "processing", "call_id": str(call.id)}
