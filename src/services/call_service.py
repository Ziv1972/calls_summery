"""Call service - orchestrates the full call processing pipeline."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.call import CallStatus, UploadSource
from src.models.summary import SummaryStatus
from src.models.transcription import TranscriptionStatus
from src.repositories.call_repository import CallRepository
from src.repositories.summary_repository import SummaryRepository
from src.repositories.transcription_repository import TranscriptionRepository
from src.services.storage_service import StorageService
from src.services.summarization_service import SummarizationService
from src.services.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessingStatus:
    """Immutable processing status."""

    call_id: uuid.UUID
    call_status: str
    transcription_status: str | None = None
    summary_status: str | None = None
    error_message: str | None = None


class CallService:
    """Orchestrates call upload, transcription, summarization."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._call_repo = CallRepository(session)
        self._transcription_repo = TranscriptionRepository(session)
        self._summary_repo = SummaryRepository(session)
        self._storage = StorageService()
        self._transcription_svc = TranscriptionService()
        self._summarization_svc = SummarizationService()

    async def upload_call(
        self,
        file_data: BinaryIO,
        original_filename: str,
        content_type: str,
        upload_source: UploadSource = UploadSource.MANUAL,
    ) -> uuid.UUID:
        """Upload a call recording to S3 and create DB record."""
        upload_result = self._storage.upload_file(
            file_data=file_data,
            original_filename=original_filename,
            content_type=content_type,
        )

        call = await self._call_repo.create({
            "filename": upload_result.s3_key.split("/")[-1],
            "original_filename": original_filename,
            "s3_key": upload_result.s3_key,
            "s3_bucket": upload_result.bucket,
            "file_size_bytes": upload_result.file_size,
            "content_type": content_type,
            "upload_source": upload_source,
            "status": CallStatus.UPLOADED,
        })

        await self._session.commit()
        logger.info("Call uploaded: %s (id=%s)", original_filename, call.id)
        return call.id

    async def process_call(
        self, call_id: uuid.UUID, language: str = "auto"
    ) -> None:
        """Run the full processing pipeline: transcribe -> summarize."""
        call = await self._call_repo.find_by_id(call_id)
        if call is None:
            raise ValueError(f"Call {call_id} not found")

        try:
            # Step 1: Transcribe
            await self._call_repo.update_status(call_id, CallStatus.TRANSCRIBING)
            await self._session.commit()

            presigned = self._storage.generate_presigned_url(call.s3_key, expires_in=7200)

            transcription_result = self._transcription_svc.transcribe_sync(
                audio_url=presigned.url,
                language_code=language if language != "auto" else None,
            )

            transcription = await self._transcription_repo.create({
                "call_id": call_id,
                "provider": "deepgram",
                "external_id": transcription_result.external_id,
                "text": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
                "duration_seconds": transcription_result.duration_seconds,
                "speakers": transcription_result.speakers,
                "words_count": transcription_result.words_count,
                "status": TranscriptionStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
            })

            await self._call_repo.update(call_id, {
                "status": CallStatus.TRANSCRIBED,
                "language_detected": transcription_result.language,
                "duration_seconds": transcription_result.duration_seconds,
            })
            await self._session.commit()

            logger.info("Transcription complete for call %s (%d words)", call_id, transcription_result.words_count)

            # Step 2: Summarize
            await self._call_repo.update_status(call_id, CallStatus.SUMMARIZING)
            await self._session.commit()

            summary_language = language if language != "auto" else transcription_result.language
            summary_result = self._summarization_svc.summarize(
                transcription_text=transcription_result.text,
                language=summary_language,
            )

            await self._summary_repo.create({
                "call_id": call_id,
                "transcription_id": transcription.id,
                "provider": "claude",
                "model": summary_result.model,
                "summary_text": summary_result.summary_text,
                "key_points": summary_result.key_points,
                "action_items": summary_result.action_items,
                "sentiment": summary_result.sentiment,
                "language": summary_language,
                "tokens_used": summary_result.tokens_used,
                "status": SummaryStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
            })

            await self._call_repo.update_status(call_id, CallStatus.COMPLETED)
            await self._session.commit()

            logger.info("Summary complete for call %s", call_id)

        except Exception as e:
            logger.error("Processing failed for call %s: %s", call_id, e)
            await self._call_repo.update_status(
                call_id, CallStatus.FAILED, error_message=str(e)
            )
            await self._session.commit()
            raise

    async def get_processing_status(self, call_id: uuid.UUID) -> ProcessingStatus:
        """Get current processing status for a call."""
        call = await self._call_repo.find_by_id(call_id)
        if call is None:
            raise ValueError(f"Call {call_id} not found")

        transcription = await self._transcription_repo.find_by_call_id(call_id)
        summary = await self._summary_repo.find_latest_by_call_id(call_id)

        return ProcessingStatus(
            call_id=call_id,
            call_status=call.status.value,
            transcription_status=transcription.status.value if transcription else None,
            summary_status=summary.status.value if summary else None,
            error_message=call.error_message,
        )
