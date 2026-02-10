"""Claude API summarization service."""

import json
import logging
from dataclasses import dataclass, field

from anthropic import Anthropic

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT_TEMPLATE = """You are an expert at analyzing phone call transcriptions. You produce detailed, actionable summaries.

{language_instruction}

RULES:
1. "summary": Write a comprehensive paragraph (5-10 sentences). Include: who called whom and why, all main topics discussed, decisions made, agreements reached, and outcome/next steps. Be specific - use names, numbers, dates, and details from the conversation.
2. "key_points": List 5-10 important points as complete sentences with context. Don't just name topics - explain what was said about each topic, by whom, and what was decided.
3. "action_items": Extract EVERY commitment, task, follow-up, or promise. Format each as "[Person/Role] - [specific action with details]". If no action items exist, use an empty array.
4. "sentiment": Overall emotional tone of the call.
5. "participants": Identify each speaker by role/name based on context (e.g., "Speaker 0 - David (Customer)", "Speaker 1 - Support Agent"). Use actual names when mentioned.

Respond ONLY with valid JSON (no markdown, no code blocks, no extra text):
{{
  "summary": "...",
  "key_points": ["...", "..."],
  "action_items": ["Person - specific action", "..."],
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "participants": ["Speaker 0 - Role/Name", "Speaker 1 - Role/Name"]
}}

CALL TRANSCRIPTION:
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
        speakers: list[dict] | None = None,
    ) -> SummaryResult:
        """Generate summary from transcription text.

        Args:
            transcription_text: Full transcription text.
            language: Target language for the summary.
            speakers: Optional list of speaker segments with 'speaker' and 'text' keys.
                      When provided, builds a speaker-labeled conversation for better context.
        """
        if not transcription_text or not transcription_text.strip():
            return SummaryResult(
                summary_text="Empty transcription - no content to summarize.",
                model=self._model,
            )

        language_instruction = LANGUAGE_INSTRUCTIONS.get(
            language, LANGUAGE_INSTRUCTIONS["auto"]
        )

        # Build rich text with speaker labels when available
        if speakers:
            conversation_lines = [f"{seg['speaker']}: {seg['text']}" for seg in speakers]
            rich_text = "\n".join(conversation_lines)
        else:
            rich_text = transcription_text

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            language_instruction=language_instruction,
            transcription_text=rich_text,
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
