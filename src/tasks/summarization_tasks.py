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
            summary_language = language if language != "auto" else (transcription.language or "auto")

            result = summarization_svc.summarize(
                transcription_text=transcription.text or "",
                language=summary_language,
                speakers=transcription.speakers if transcription.speakers else None,
            )

            # Save summary
            from datetime import datetime, timezone

            summary = Summary(
                call_id=call_id,
                transcription_id=transcription_id,
                provider="claude",
                model=result.model,
                summary_text=result.summary_text,
                key_points=result.key_points,
                action_items=result.action_items,
                sentiment=result.sentiment,
                language=summary_language,
                tokens_used=result.tokens_used,
                status=SummaryStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            session.add(summary)

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
