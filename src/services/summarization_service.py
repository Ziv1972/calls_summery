"""Claude API summarization service."""

import json
import logging
from dataclasses import dataclass, field

from anthropic import Anthropic

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT_TEMPLATE = """You are an expert at analyzing phone call transcriptions and producing detailed, actionable summaries.

Analyze the following phone call transcription thoroughly.

{language_instruction}

IMPORTANT RULES:
- The "summary" field must be a detailed paragraph (5-10 sentences) covering the main topics, decisions, and outcomes of the call. Do NOT write just 1-2 sentences.
- List ALL key points discussed, not just the main one. Aim for 5-10 key points for longer calls.
- Extract EVERY action item, commitment, or follow-up mentioned. Include who is responsible if mentioned.
- If speakers are identified (e.g. "Speaker 0", "Speaker 1"), try to identify their roles based on context (e.g. "customer", "agent", "manager").

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "summary": "Detailed paragraph summarizing the entire call...",
  "key_points": ["Key point 1", "Key point 2", "Key point 3", ...],
  "action_items": ["Action item 1", "Action item 2", ...],
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "participants": ["Role/Name 1", "Role/Name 2", ...]
}}

Transcription:
{transcription_text}
"""

LANGUAGE_INSTRUCTIONS = {
    "auto": "Respond in the same language as the transcription.",
    "he": "Respond in Hebrew (עברית). All text in the JSON should be in Hebrew.",
    "en": "Respond in English. All text in the JSON should be in English.",
}


@dataclass(frozen=True)
class SummaryResult:
    """Immutable summary result."""

    summary_text: str
    key_points: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    participants: list[str] = field(default_factory=list)
    tokens_used: int = 0
    model: str = ""


class SummarizationService:
    """Claude API summarization service."""

    def __init__(self):
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model

    def summarize(
        self,
        transcription_text: str,
        language: str = "auto",
    ) -> SummaryResult:
        """Generate summary from transcription text."""
        if not transcription_text or not transcription_text.strip():
            return SummaryResult(
                summary_text="Empty transcription - no content to summarize.",
                model=self._model,
            )

        language_instruction = LANGUAGE_INSTRUCTIONS.get(
            language, LANGUAGE_INSTRUCTIONS["auto"]
        )

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            language_instruction=language_instruction,
            transcription_text=transcription_text,
        )

        logger.info("Requesting summary from %s (language=%s)", self._model, language)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        parsed = self._parse_response(raw_text)

        return SummaryResult(
            summary_text=parsed.get("summary", raw_text),
            key_points=parsed.get("key_points", []),
            action_items=parsed.get("action_items", []),
            sentiment=parsed.get("sentiment", "neutral"),
            participants=parsed.get("participants", []),
            tokens_used=tokens_used,
            model=self._model,
        )

    def _parse_response(self, text: str) -> dict:
        """Parse JSON response from Claude. Falls back to raw text."""
        # Try to extract JSON from the response
        try:
            # Handle case where response includes markdown code block
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse JSON from Claude response, using raw text")
            return {"summary": text}
