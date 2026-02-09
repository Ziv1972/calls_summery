"""Celery tasks for transcription processing."""

import logging

from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_transcription(self, call_id: str, language: str = "auto"):
    """Process transcription for a call (async Celery task).

    This task runs synchronously within Celery worker.
    Uses sync DB session since Celery doesn't support async natively.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from src.config.settings import get_settings
    from src.models.call import Call, CallStatus
    from src.models.transcription import Transcription, TranscriptionStatus
    from src.services.storage_service import StorageService
    from src.services.transcription_service import TranscriptionService

    settings = get_settings()
    # Convert async URL to sync for Celery worker
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+psycopg2", "postgresql")
    engine = create_engine(sync_url)

    try:
        with Session(engine) as session:
            call = session.get(Call, call_id)
            if call is None:
                logger.error("Call %s not found", call_id)
                return

            # Update status
            call.status = CallStatus.TRANSCRIBING
            session.commit()

            # Get presigned URL
            storage = StorageService()
            presigned = storage.generate_presigned_url(call.s3_key, expires_in=7200)

            # Transcribe
            transcription_svc = TranscriptionService()
            result = transcription_svc.transcribe_sync(
                audio_url=presigned.url,
                language_code=language if language != "auto" else None,
            )

            # Save transcription
            from datetime import datetime, timezone

            transcription = Transcription(
                call_id=call_id,
                provider="deepgram",
                external_id=result.external_id,
                text=result.text,
                confidence=result.confidence,
                language=result.language,
                duration_seconds=result.duration_seconds,
                speakers=result.speakers,
                words_count=result.words_count,
                status=TranscriptionStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            session.add(transcription)

            call.status = CallStatus.TRANSCRIBED
            call.language_detected = result.language
            call.duration_seconds = result.duration_seconds
            session.commit()

            logger.info("Transcription complete for call %s", call_id)

            # Chain to summarization
            from src.tasks.summarization_tasks import process_summarization

            process_summarization.delay(call_id, str(transcription.id), language)

    except Exception as exc:
        logger.error("Transcription failed for call %s: %s", call_id, exc)
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
