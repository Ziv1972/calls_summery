"""Claude API summarization service."""

import json
import logging
from dataclasses import dataclass, field

from anthropic import Anthropic

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT_TEMPLATE = """You summarize phone call transcriptions. Report ONLY what was said - no opinions, no analysis, no recommendations.

{language_instruction}

RULES:
1. "summary": Write a factual paragraph (3-7 sentences). State: who spoke, the purpose of the call, what was discussed, what was decided, and any next steps. Use names, numbers, and dates mentioned in the call. Do NOT add your own interpretation or assessment.
2. "key_points": List 3-7 important points as factual sentences. Report what was said by whom and what was decided. Do NOT add context or analysis that wasn't in the conversation.
3. "action_items": Extract commitments, tasks, or promises made during the call. Format: "[Person] - [action]". Empty array if none.
4. "sentiment": The emotional tone of the call (positive/neutral/negative/mixed).
5. "participants": Identify speakers by name/role based on context.

CRITICAL: Write ONLY in the specified language. Never mix languages. If instructed to write in Hebrew, every word must be in Hebrew (except proper nouns like company names).

Respond ONLY with valid JSON:
{{
  "summary": "...",
  "key_points": ["...", "..."],
  "action_items": ["Person - action", "..."],
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "participants": ["Speaker 0 - Name/Role", "Speaker 1 - Name/Role"]
}}

CALL TRANSCRIPTION:
{transcription_text}
"""

LANGUAGE_INSTRUCTIONS = {
    "auto": "Respond in the same language as the transcription.",
    "he": "חובה לכתוב בעברית בלבד. כל הטקסט ב-JSON חייב להיות בעברית. אסור לערבב עברית ואנגלית.",
    "en": "Respond in English only. All text in the JSON must be in English.",
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
            max_tokens=1024,
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
