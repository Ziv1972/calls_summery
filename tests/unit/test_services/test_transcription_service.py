"""Tests for Deepgram transcription service."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.transcription_service import TranscriptionResult, TranscriptionService


class TestTranscriptionResult:
    """Test TranscriptionResult immutable dataclass."""

    def test_create_result(self):
        result = TranscriptionResult(
            text="hello world",
            confidence=0.95,
            language="en",
            duration_seconds=120.5,
            external_id="req-123",
            words_count=2,
            speakers=[{"speaker": "Speaker 0", "text": "hello", "start": 0, "end": 1000}],
        )
        assert result.text == "hello world"
        assert result.confidence == 0.95
        assert result.language == "en"
        assert result.duration_seconds == 120.5
        assert result.words_count == 2
        assert len(result.speakers) == 1

    def test_result_is_immutable(self):
        result = TranscriptionResult(
            text="t", confidence=0.5, language="en",
            duration_seconds=1.0, external_id="x", words_count=1,
        )
        with pytest.raises(AttributeError):
            result.text = "modified"

    def test_default_speakers_empty_list(self):
        result = TranscriptionResult(
            text="t", confidence=0.5, language="en",
            duration_seconds=1.0, external_id="x", words_count=1,
        )
        assert result.speakers == []


class TestTranscriptionService:
    """Test TranscriptionService with mocked Deepgram."""

    def _mock_deepgram_response(self):
        """Create a mock Deepgram response."""
        utterance = MagicMock()
        utterance.speaker = 0
        utterance.transcript = "Hello, how are you?"
        utterance.start = 0.5
        utterance.end = 2.3

        alternative = MagicMock()
        alternative.transcript = "Hello, how are you?"
        alternative.confidence = 0.97

        channel = MagicMock()
        channel.alternatives = [alternative]
        channel.detected_language = "en"

        result = MagicMock()
        result.channels = [channel]
        result.utterances = [utterance]

        response = MagicMock()
        response.results = result
        response.metadata = MagicMock()
        response.metadata.duration = 45.5
        response.metadata.request_id = "req-abc"
        response.metadata.language = "en"

        return response

    @patch("src.services.transcription_service.DeepgramClient")
    @patch("src.services.transcription_service.get_settings")
    def test_transcribe_sync_with_language(self, mock_settings, mock_dg_client):
        mock_settings.return_value = MagicMock(deepgram_api_key="test-key")
        mock_response = self._mock_deepgram_response()
        mock_instance = MagicMock()
        mock_instance.listen.v1.media.transcribe_url.return_value = mock_response
        mock_dg_client.return_value = mock_instance

        svc = TranscriptionService()
        result = svc.transcribe_sync("https://s3.test/audio.mp3", language_code="he")

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello, how are you?"
        assert result.confidence == 0.97
        assert result.language == "en"
        assert result.duration_seconds == 45.5
        assert result.external_id == "req-abc"
        assert len(result.speakers) == 1
        assert result.speakers[0]["speaker"] == "Speaker 0"

        # Verify language was passed
        call_kwargs = mock_instance.listen.v1.media.transcribe_url.call_args
        assert call_kwargs.kwargs.get("language") == "he"

    @patch("src.services.transcription_service.DeepgramClient")
    @patch("src.services.transcription_service.get_settings")
    def test_transcribe_sync_auto_detect(self, mock_settings, mock_dg_client):
        mock_settings.return_value = MagicMock(deepgram_api_key="test-key")
        mock_response = self._mock_deepgram_response()
        mock_instance = MagicMock()
        mock_instance.listen.v1.media.transcribe_url.return_value = mock_response
        mock_dg_client.return_value = mock_instance

        svc = TranscriptionService()
        result = svc.transcribe_sync("https://s3.test/audio.mp3", language_code=None)

        assert isinstance(result, TranscriptionResult)
        call_kwargs = mock_instance.listen.v1.media.transcribe_url.call_args
        assert call_kwargs.kwargs.get("detect_language") is True
        assert "language" not in call_kwargs.kwargs

    @patch("src.services.transcription_service.DeepgramClient")
    @patch("src.services.transcription_service.get_settings")
    def test_transcribe_file_sync(self, mock_settings, mock_dg_client):
        mock_settings.return_value = MagicMock(deepgram_api_key="test-key")
        mock_response = self._mock_deepgram_response()
        mock_instance = MagicMock()
        mock_instance.listen.v1.media.transcribe_file.return_value = mock_response
        mock_dg_client.return_value = mock_instance

        svc = TranscriptionService()
        result = svc.transcribe_file_sync(b"fake-audio", "audio/mpeg", language_code="en")

        assert isinstance(result, TranscriptionResult)
        assert result.words_count == 4  # "Hello, how are you?" split by spaces

    @patch("src.services.transcription_service.DeepgramClient")
    @patch("src.services.transcription_service.get_settings")
    def test_parse_response_no_utterances(self, mock_settings, mock_dg_client):
        mock_settings.return_value = MagicMock(deepgram_api_key="test-key")

        alternative = MagicMock()
        alternative.transcript = "some text"
        alternative.confidence = 0.85

        channel = MagicMock()
        channel.alternatives = [alternative]
        channel.detected_language = "he"

        result_mock = MagicMock()
        result_mock.channels = [channel]
        result_mock.utterances = None

        response = MagicMock()
        response.results = result_mock
        response.metadata = MagicMock()
        response.metadata.duration = 10.0
        response.metadata.request_id = "req-xyz"

        mock_instance = MagicMock()
        mock_instance.listen.v1.media.transcribe_url.return_value = response
        mock_dg_client.return_value = mock_instance

        svc = TranscriptionService()
        result = svc.transcribe_sync("https://test/audio.mp3")

        assert result.speakers == []
        assert result.text == "some text"

    @patch("src.services.transcription_service.DeepgramClient")
    @patch("src.services.transcription_service.get_settings")
    def test_parse_response_empty_transcript(self, mock_settings, mock_dg_client):
        mock_settings.return_value = MagicMock(deepgram_api_key="test-key")

        alternative = MagicMock()
        alternative.transcript = ""
        alternative.confidence = 0.0

        channel = MagicMock()
        channel.alternatives = [alternative]
        channel.detected_language = None
        # Simulate missing detected_language attribute
        del channel.detected_language

        result_mock = MagicMock()
        result_mock.channels = [channel]
        result_mock.utterances = []

        response = MagicMock()
        response.results = result_mock
        response.metadata = MagicMock()
        response.metadata.duration = 0.0
        response.metadata.request_id = ""
        response.metadata.language = None

        mock_instance = MagicMock()
        mock_instance.listen.v1.media.transcribe_url.return_value = response
        mock_dg_client.return_value = mock_instance

        svc = TranscriptionService()
        result = svc.transcribe_sync("https://test/empty.mp3")

        assert result.text == ""
        assert result.words_count == 0
