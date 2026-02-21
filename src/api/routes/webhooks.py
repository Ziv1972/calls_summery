"""Webhook endpoints for S3 events and external callbacks."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class S3EventPayload(BaseModel):
    """S3 event notification payload (simplified)."""

    bucket: str
    key: str
    size: int
    content_type: str = "audio/mpeg"
    original_filename: str | None = None
    upload_source: str = "auto_agent"


@router.post("/s3-upload")
async def s3_upload_event(
    payload: S3EventPayload,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Handle S3 upload event from local agent or Android app.

    Requires authentication (JWT or API key).
    The call is assigned to the authenticated user.
    """
    from src.models.call import CallStatus, UploadSource
    from src.repositories.call_repository import CallRepository

    call_repo = CallRepository(session)

    # Check if already processed
    existing = await call_repo.find_by_s3_key(payload.key)
    if existing is not None:
        logger.info("S3 key %s already registered, skipping", payload.key)
        return {"status": "already_exists", "call_id": str(existing.id)}

    # Create call record assigned to current user
    filename = payload.key.split("/")[-1]
    original = payload.original_filename or filename
    call = await call_repo.create({
        "filename": filename,
        "original_filename": original,
        "s3_key": payload.key,
        "s3_bucket": payload.bucket,
        "file_size_bytes": payload.size,
        "content_type": payload.content_type,
        "upload_source": UploadSource(payload.upload_source) if payload.upload_source in [e.value for e in UploadSource] else UploadSource.AUTO_AGENT,
        "status": CallStatus.UPLOADED,
        "user_id": current_user.id,
    })
    await session.commit()

    # Read language preference from user settings
    from src.models.settings import UserSettings

    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()
    language = user_settings.summary_language if user_settings else "he"

    # Trigger processing
    from src.tasks.transcription_tasks import process_transcription

    process_transcription.delay(str(call.id), language)

    logger.info("Auto-upload registered: %s (call_id=%s, user=%s)", payload.key, call.id, current_user.id)
    return {"status": "processing", "call_id": str(call.id)}


async def verify_twilio_signature(request: Request) -> None:
    """Validate Twilio request signature to prevent spoofing.

    Skips validation if TWILIO_AUTH_TOKEN is not configured (dev mode).
    """
    from src.config.settings import get_settings

    settings = get_settings()
    auth_token = settings.twilio_auth_token
    if not auth_token:
        logger.warning("Twilio auth token not configured, skipping signature validation")
        return

    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        logger.warning("Twilio package not installed, skipping signature validation")
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form_data = dict(await request.form())

    validator = RequestValidator(auth_token)
    if not validator.validate(url, form_data, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.post("/twilio/status")
async def twilio_status_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_twilio_signature),
):
    """Handle Twilio message delivery status callbacks.

    Twilio POSTs status updates (delivered, failed, undelivered) here.
    No auth required — validated via Twilio request signature.
    """
    from src.models.notification import Notification, NotificationStatus

    form_data = await request.form()
    message_sid = form_data.get("MessageSid", "")
    message_status = form_data.get("MessageStatus", "")
    error_code = form_data.get("ErrorCode")

    if not message_sid:
        return {"status": "ignored"}

    result = await session.execute(
        select(Notification).where(Notification.external_id == message_sid)
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        logger.warning("Twilio status callback for unknown SID: %s", message_sid)
        return {"status": "not_found"}

    status_map = {
        "delivered": NotificationStatus.DELIVERED,
        "read": NotificationStatus.DELIVERED,
        "failed": NotificationStatus.FAILED,
        "undelivered": NotificationStatus.FAILED,
    }

    new_status = status_map.get(message_status)
    if new_status is not None:
        notification.status = new_status
        if error_code:
            notification.error_message = f"Twilio error code: {error_code}"
        await session.commit()
        logger.info("Notification %s status updated to %s (SID=%s)", notification.id, new_status, message_sid)

    return {"status": "updated"}
