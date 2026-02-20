"""Celery tasks for summarization processing."""

import logging

from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_summarization(
    self, call_id: str, transcription_id: str, language: str = "auto"
):
    """Generate summary for a transcribed call (async Celery task)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from src.config.settings import get_settings
    from src.models.call import Call, CallStatus
    from src.models.summary import Summary, SummaryStatus
    from src.models.transcription import Transcription
    from src.services.summarization_service import SummarizationService

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
    engine = create_engine(sync_url)

    try:
        with Session(engine) as session:
            call = session.get(Call, call_id)
            transcription = session.get(Transcription, transcription_id)

            if call is None or transcription is None:
                logger.error("Call %s or transcription %s not found", call_id, transcription_id)
                return

            call.status = CallStatus.SUMMARIZING
            session.commit()

            # Summarize - pass speaker segments for better context
            summarization_svc = SummarizationService()
            # Resolve language: use explicit setting, or detected language, or default to Hebrew
            if language not in ("auto", "unknown"):
                summary_language = language
            elif transcription.language and transcription.language not in ("auto", "unknown"):
                summary_language = transcription.language
            else:
                summary_language = "he"

            result = summarization_svc.summarize(
                transcription_text=transcription.text or "",
                language=summary_language,
                speakers=transcription.speakers if transcription.speakers else None,
            )

            # Save summary with structured data
            from datetime import datetime, timezone

            summary = Summary(
                call_id=call_id,
                transcription_id=transcription_id,
                provider="claude",
                model=result.model,
                summary_text=result.summary_text,
                key_points=result.key_points,
                action_items=result.action_items,
                structured_actions=result.structured_actions,
                participants_details=result.participants_details,
                topics=result.topics,
                sentiment=result.sentiment,
                language=summary_language,
                tokens_used=result.tokens_used,
                status=SummaryStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            session.add(summary)

            # Auto-link call to contact based on extracted phone numbers
            _try_link_contact(session, call, result.participants_details)

            call.status = CallStatus.COMPLETED
            session.commit()

            logger.info("Summary complete for call %s", call_id)

            # Chain to notification if configured
            from src.tasks.notification_tasks import send_notifications

            send_notifications.delay(call_id, str(summary.id))

    except Exception as exc:
        logger.error("Summarization failed for call %s: %s", call_id, exc)
        try:
            with Session(engine) as session:
                call = session.get(Call, call_id)
                if call:
                    call.status = CallStatus.FAILED
                    call.error_message = str(exc)[:2000]
                    session.commit()
        except Exception:
            logger.exception("Failed to update call status")
        raise self.retry(exc=exc)


def _try_link_contact(session, call, participants_details: list[dict]) -> None:
    """Try to link a call to a contact based on phone numbers in participants."""
    if not participants_details or call.user_id is None:
        return

    try:
        from src.models.contact import Contact
        from src.services.contact_service import extract_phone_numbers

        phones = extract_phone_numbers(participants_details)
        if not phones:
            return

        # Search for matching contacts (sync query for Celery)
        for phone in phones:
            contact = session.query(Contact).filter(
                Contact.user_id == call.user_id,
                Contact.phone_number == phone,
            ).first()
            if contact:
                call.contact_id = contact.id
                call.caller_phone = phone
                logger.info("Linked call %s to contact %s (%s)", call.id, contact.id, contact.name)
                return

        # Store the first extracted phone even if no contact match
        if phones:
            call.caller_phone = phones[0]
    except Exception:
        logger.exception("Failed to link contact for call %s", call.id)
