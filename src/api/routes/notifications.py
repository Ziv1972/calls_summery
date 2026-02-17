"""Notification API endpoints - list and retry notifications."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.api.middleware.auth import get_current_user
from src.models.user import User
from src.repositories.notification_repository import NotificationRepository
from src.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """Notification response schema."""

    id: uuid.UUID
    summary_id: uuid.UUID
    delivery_type: str
    recipient: str
    status: str
    external_id: str | None = None
    error_message: str | None = None
    sent_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List notifications for the current user."""
    repo = NotificationRepository(session)
    result = await repo.find_by_user(current_user.id, page=page, page_size=page_size)

    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("/{notification_id}/retry")
async def retry_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retry a failed notification."""
    from src.models.call import Call
    from src.models.notification import DeliveryType, Notification, NotificationStatus
    from src.models.summary import Summary

    repo = NotificationRepository(session)
    notification = await repo.find_by_id(notification_id)

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Verify ownership via summary -> call -> user
    summary = await session.get(Summary, notification.summary_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    call = await session.get(Call, summary.call_id)
    if call is None or call.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.status != NotificationStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed notifications can be retried")

    # Re-send based on delivery type
    if notification.delivery_type == DeliveryType.EMAIL:
        from src.services.email_service import EmailService

        svc = EmailService()
        result = svc.send_summary(
            to_email=notification.recipient,
            call_filename=call.original_filename,
            summary_text=summary.summary_text or "",
            key_points=summary.key_points,
            action_items=summary.action_items,
        )
        if result.success:
            notification.status = NotificationStatus.SENT
            notification.external_id = result.message_id
            notification.error_message = None
        else:
            notification.error_message = result.error

    elif notification.delivery_type == DeliveryType.WHATSAPP:
        from src.services.whatsapp_service import WhatsAppService

        svc = WhatsAppService()
        result = svc.send_summary(
            to_number=notification.recipient,
            call_filename=call.original_filename,
            summary_text=summary.summary_text or "",
            key_points=summary.key_points,
            action_items=summary.action_items,
        )
        if result.success:
            notification.status = NotificationStatus.SENT
            notification.external_id = result.message_sid
            notification.error_message = None
        else:
            notification.error_message = result.error

    await session.commit()
    logger.info("Retry notification %s: %s", notification_id, notification.status)

    return {
        "success": notification.status == NotificationStatus.SENT,
        "status": notification.status.value,
        "error": notification.error_message,
    }
