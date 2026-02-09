"""Tests for summarization service."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.summarization_service import SummarizationService, SummaryResult


class TestSummarizationService:
    """Test Claude API summarization."""

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_summarize_returns_immutable_result(
        self, mock_anthropic_cls, mock_settings, sample_transcription_text, sample_summary_json
    ):
        """Summarize should return a frozen SummaryResult."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_summary_json))]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize(sample_transcription_text, language="en")

        assert isinstance(result, SummaryResult)
        assert result.summary_text == sample_summary_json["summary"]
        assert result.key_points == sample_summary_json["key_points"]
        assert result.action_items == sample_summary_json["action_items"]
        assert result.sentiment == "positive"
        assert result.tokens_used == 150
        assert result.model == "claude-haiku-4-5-20251001"

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_summarize_empty_text(self, mock_anthropic_cls, mock_settings):
        """Empty transcription should return early without API call."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        svc = SummarizationService()
        result = svc.summarize("", language="en")

        assert "Empty transcription" in result.summary_text
        mock_anthropic_cls.return_value.messages.create.assert_not_called()

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_summarize_handles_markdown_json(
        self, mock_anthropic_cls, mock_settings, sample_transcription_text, sample_summary_json
    ):
        """Should parse JSON wrapped in markdown code blocks."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        wrapped_json = f"```json\n{json.dumps(sample_summary_json)}\n```"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=wrapped_json)]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize(sample_transcription_text)

        assert result.summary_text == sample_summary_json["summary"]

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_summarize_handles_unparseable_response(
        self, mock_anthropic_cls, mock_settings, sample_transcription_text
    ):
        """Should fall back to raw text when JSON parsing fails."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        raw_text = "This is a plain text summary without JSON."
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=raw_text)]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize(sample_transcription_text)

        assert result.summary_text == raw_text
