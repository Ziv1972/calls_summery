"""Deepgram transcription service."""

import logging
from dataclasses import dataclass, field

from deepgram import DeepgramClient, ListenV1Response

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionResult:
    """Immutable transcription result."""

    text: str
    confidence: float
    language: str
    duration_seconds: float
    external_id: str
    words_count: int
    speakers: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class TranscriptionJob:
    """Immutable job reference."""

    job_id: str
    status: str


class TranscriptionService:
    """Deepgram Nova-3 transcription service."""

    def __init__(self):
        settings = get_settings()
        self._client = DeepgramClient(api_key=settings.deepgram_api_key)

    def transcribe_sync(
        self, audio_url: str, language_code: str | None = None
    ) -> TranscriptionResult:
        """Transcribe audio from URL (blocking).

        Uses Deepgram Nova-3 with speaker diarization.
        """
        options = {
            "model": "nova-3",
            "smart_format": True,
            "diarize": True,
            "utterances": True,
            "punctuate": True,
        }

        if language_code:
            options["language"] = language_code
        else:
            options["detect_language"] = True

        logger.info("Submitting transcription to Deepgram for %s", audio_url[:80])

        response = self._client.listen.rest.v("1").transcribe_url(
            {"url": audio_url},
            options,
        )

        return self._parse_response(response)

    def transcribe_file_sync(
        self, file_data: bytes, mimetype: str, language_code: str | None = None
    ) -> TranscriptionResult:
        """Transcribe audio from file bytes (blocking)."""
        options = {
            "model": "nova-3",
            "smart_format": True,
            "diarize": True,
            "utterances": True,
            "punctuate": True,
        }

        if language_code:
            options["language"] = language_code
        else:
            options["detect_language"] = True

        logger.info("Submitting file transcription to Deepgram (%d bytes)", len(file_data))

        source = {"buffer": file_data, "mimetype": mimetype}
        response = self._client.listen.rest.v("1").transcribe_file(
            source,
            options,
        )

        return self._parse_response(response)

    def _parse_response(self, response: ListenV1Response) -> TranscriptionResult:
        """Parse Deepgram response into immutable result."""
        result = response.results
        channel = result.channels[0]
        alternative = channel.alternatives[0]

        text = alternative.transcript or ""
        confidence = alternative.confidence or 0.0
        words_count = len(text.split()) if text else 0

        # Extract detected language
        language = "unknown"
        if hasattr(channel, "detected_language") and channel.detected_language:
            language = channel.detected_language
        elif hasattr(response, "metadata") and hasattr(response.metadata, "language"):
            language = response.metadata.language or "unknown"

        # Extract duration
        duration_seconds = 0.0
        if hasattr(response, "metadata") and hasattr(response.metadata, "duration"):
            duration_seconds = response.metadata.duration or 0.0

        # Extract request ID as external reference
        request_id = ""
        if hasattr(response, "metadata") and hasattr(response.metadata, "request_id"):
            request_id = response.metadata.request_id or ""

        # Extract speaker segments from utterances
        speakers = []
        if hasattr(result, "utterances") and result.utterances:
            for utterance in result.utterances:
                speakers.append({
                    "speaker": f"Speaker {utterance.speaker}",
                    "text": utterance.text,
                    "start": int(utterance.start * 1000),
                    "end": int(utterance.end * 1000),
                })

        logger.info(
            "Deepgram transcription complete: %d words, %.1fs, language=%s, %d speaker segments",
            words_count, duration_seconds, language, len(speakers),
        )

        return TranscriptionResult(
            text=text,
            confidence=confidence,
            language=language,
            duration_seconds=duration_seconds,
            external_id=request_id,
            words_count=words_count,
            speakers=speakers,
        )
