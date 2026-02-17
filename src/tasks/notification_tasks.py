"""Celery tasks for notification delivery (email/WhatsApp)."""

import logging
from datetime import datetime, timezone

from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_notifications(self, call_id: str, summary_id: str):
    """Send notifications for a completed summary."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from src.config.settings import get_settings
    from src.models.call import Call
    from src.models.notification import DeliveryType, Notification, NotificationStatus
    from src.models.settings import NotificationMethod, UserSettings
    from src.models.summary import Summary

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
    engine = create_engine(sync_url)

    try:
        with Session(engine) as session:
            call = session.get(Call, call_id)
            summary = session.get(Summary, summary_id)

            if call is None or summary is None:
                logger.error("Call %s or summary %s not found", call_id, summary_id)
                return

            # Get user settings by call's user_id
            if call.user_id is not None:
                user_settings = session.query(UserSettings).filter(
                    UserSettings.user_id == call.user_id
                ).first()
            else:
                # Fallback for legacy calls without user_id
                user_settings = session.query(UserSettings).first()

            if user_settings is None or not user_settings.notify_on_complete:
                logger.info("Notifications disabled, skipping for call %s", call_id)
                return

            method = user_settings.notification_method

            # Send email
            if method in (NotificationMethod.EMAIL, NotificationMethod.BOTH):
                if user_settings.email_recipient:
                    _send_email_notification(
                        session, summary, call, user_settings.email_recipient
                    )

            # Send WhatsApp
            if method in (NotificationMethod.WHATSAPP, NotificationMethod.BOTH):
                if user_settings.whatsapp_recipient:
                    _send_whatsapp_notification(
                        session, summary, call, user_settings.whatsapp_recipient
                    )

            session.commit()

    except Exception as exc:
        logger.error("Notification failed for call %s: %s", call_id, exc)
        raise self.retry(exc=exc)


def _send_email_notification(session, summary, call, recipient: str):
    """Send email notification and record result."""
    from src.models.notification import DeliveryType, Notification, NotificationStatus
    from src.services.email_service import EmailService

    email_svc = EmailService()
    result = email_svc.send_summary(
        to_email=recipient,
        call_filename=call.original_filename,
        summary_text=summary.summary_text or "",
        key_points=summary.key_points,
        action_items=summary.action_items,
    )

    notification = Notification(
        summary_id=summary.id,
        delivery_type=DeliveryType.EMAIL,
        recipient=recipient,
        status=NotificationStatus.SENT if result.success else NotificationStatus.FAILED,
        external_id=result.message_id,
        error_message=result.error,
        sent_at=datetime.now(timezone.utc) if result.success else None,
    )
    session.add(notification)
    logger.info("Email notification %s for call %s", "sent" if result.success else "failed", call.id)


def _send_whatsapp_notification(session, summary, call, recipient: str):
    """Send WhatsApp notification and record result."""
    from src.models.notification import DeliveryType, Notification, NotificationStatus
    from src.services.whatsapp_service import WhatsAppService

    wa_svc = WhatsAppService()
    result = wa_svc.send_summary(
        to_number=recipient,
        call_filename=call.original_filename,
        summary_text=summary.summary_text or "",
        key_points=summary.key_points,
        action_items=summary.action_items,
    )

    notification = Notification(
        summary_id=summary.id,
        delivery_type=DeliveryType.WHATSAPP,
        recipient=recipient,
        status=NotificationStatus.SENT if result.success else NotificationStatus.FAILED,
        external_id=result.message_sid,
        error_message=result.error,
        sent_at=datetime.now(timezone.utc) if result.success else None,
    )
    session.add(notification)
    logger.info("WhatsApp notification %s for call %s", "sent" if result.success else "failed", call.id)
