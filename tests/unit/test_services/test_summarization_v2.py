"""Tests for enhanced summarization service with structured actions."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.summarization_service import SummarizationService, SummaryResult


class TestStructuredActions:
    """Test structured action parsing and validation."""

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_parses_structured_actions(
        self, mock_anthropic_cls, mock_settings, sample_summary_json_v2
    ):
        """Should parse structured_actions from Claude response."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_summary_json_v2))]
        mock_response.usage.input_tokens = 200
        mock_response.usage.output_tokens = 100

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test transcription", language="en")

        assert len(result.structured_actions) == 3
        assert result.structured_actions[0]["type"] == "send_email"
        assert result.structured_actions[1]["type"] == "calendar_event"
        assert result.structured_actions[2]["type"] == "reminder"

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_parses_participants_details(
        self, mock_anthropic_cls, mock_settings, sample_summary_json_v2
    ):
        """Should parse rich participant details."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_summary_json_v2))]
        mock_response.usage.input_tokens = 200
        mock_response.usage.output_tokens = 100

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test transcription", language="en")

        assert len(result.participants_details) == 2
        assert result.participants_details[0]["name"] == "David"
        assert result.participants_details[0]["role"] == "Client"
        assert result.participants_details[0]["phone"] == "+972501234567"
        assert result.participants_details[1]["name"] is None

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_parses_topics(
        self, mock_anthropic_cls, mock_settings, sample_summary_json_v2
    ):
        """Should parse topics list."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_summary_json_v2))]
        mock_response.usage.input_tokens = 200
        mock_response.usage.output_tokens = 100

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test transcription", language="en")

        assert result.topics == ["project deadline", "specs delivery", "timeline"]

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_legacy_participants_format(
        self, mock_anthropic_cls, mock_settings, sample_summary_json_v2
    ):
        """Should generate legacy string-format participants for backwards compatibility."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_summary_json_v2))]
        mock_response.usage.input_tokens = 200
        mock_response.usage.output_tokens = 100

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test transcription", language="en")

        # Legacy format should be "Speaker 0 - David - Client"
        assert len(result.participants) == 2
        assert "David" in result.participants[0]
        assert "Client" in result.participants[0]

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_filters_invalid_action_types(self, mock_anthropic_cls, mock_settings):
        """Should filter out actions with unknown types."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        response_json = {
            "summary": "Test summary",
            "key_points": [],
            "action_items": [],
            "structured_actions": [
                {"type": "send_email", "description": "Valid", "details": {}, "confidence": 0.9},
                {"type": "hack_nasa", "description": "Invalid", "details": {}, "confidence": 0.5},
                {"type": "task", "description": "Also valid", "details": {}, "confidence": 0.8},
            ],
            "participants": [],
            "topics": [],
            "sentiment": "neutral",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response_json))]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test transcription")

        assert len(result.structured_actions) == 2
        types = [a["type"] for a in result.structured_actions]
        assert "hack_nasa" not in types

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_clamps_confidence(self, mock_anthropic_cls, mock_settings):
        """Should clamp confidence values to 0.0-1.0 range."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        response_json = {
            "summary": "Test",
            "key_points": [],
            "action_items": [],
            "structured_actions": [
                {"type": "task", "description": "High", "details": {}, "confidence": 1.5},
                {"type": "task", "description": "Low", "details": {}, "confidence": -0.3},
            ],
            "participants": [],
            "topics": [],
            "sentiment": "neutral",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response_json))]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test")

        assert result.structured_actions[0]["confidence"] == 1.0
        assert result.structured_actions[1]["confidence"] == 0.0

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_invalid_sentiment_defaults_to_neutral(self, mock_anthropic_cls, mock_settings):
        """Should default invalid sentiment to neutral."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        response_json = {
            "summary": "Test",
            "key_points": [],
            "action_items": [],
            "structured_actions": [],
            "participants": [],
            "topics": [],
            "sentiment": "very_happy",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response_json))]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        result = svc.summarize("Test")

        assert result.sentiment == "neutral"

    @patch("src.services.summarization_service.get_settings")
    @patch("src.services.summarization_service.Anthropic")
    def test_max_tokens_increased(self, mock_anthropic_cls, mock_settings):
        """Max tokens should be 2048 for richer output."""
        mock_settings.return_value = MagicMock(
            anthropic_api_key="test-key",
            claude_model="claude-haiku-4-5-20251001",
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "test"}')]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        svc = SummarizationService()
        svc.summarize("Test transcription")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["max_tokens"] == 2048
