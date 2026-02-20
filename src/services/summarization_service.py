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
5. "participants": Identify speakers with details. For each speaker, extract:
   - "speaker_label": The diarization label (e.g., "Speaker 0")
   - "name": Inferred name from context (e.g., "Thanks, David" means that speaker is David). Use null if unknown.
   - "role": Inferred role (e.g., "client", "sales rep", "manager"). Use null if unknown.
   - "phone": Phone number if mentioned in the call. Use null if not mentioned.
6. "structured_actions": Extract actionable follow-ups from the call. Each action must have:
   - "type": One of "calendar_event", "send_email", "send_whatsapp", "reminder", "task"
   - "description": Human-readable description of the action
   - "details": Type-specific fields (see examples below)
   - "confidence": 0.0-1.0 how certain you are this action was agreed upon
   Empty array if no actions detected.
7. "topics": List 2-5 topic tags that describe what the call was about (e.g., "budget", "contract", "scheduling").

STRUCTURED_ACTIONS EXAMPLES:
- calendar_event: {{"type": "calendar_event", "description": "Meeting with David", "details": {{"title": "Follow-up meeting", "date": "2026-02-25", "time": "14:00", "duration_minutes": 60, "participants": ["David"]}}, "confidence": 0.9}}
- send_email: {{"type": "send_email", "description": "Send proposal to David", "details": {{"to_name": "David", "to_email": "david@example.com", "subject": "Project Proposal", "body_outline": "Thank for call, attach proposal"}}, "confidence": 0.8}}
- send_whatsapp: {{"type": "send_whatsapp", "description": "Send contract via WhatsApp", "details": {{"to_name": "David", "phone": "+972501234567", "message_outline": "Sending contract as discussed"}}, "confidence": 0.7}}
- reminder: {{"type": "reminder", "description": "Follow up if no response", "details": {{"date": "2026-02-28", "time": "09:00", "note": "Check if David responded to proposal"}}, "confidence": 0.8}}
- task: {{"type": "task", "description": "Prepare budget breakdown", "details": {{"title": "Prepare budget breakdown", "due_date": "2026-02-24", "priority": "high", "assignee": "Self"}}, "confidence": 0.9}}

Only include structured_actions when actions were clearly discussed or committed to. Do NOT invent actions.

CRITICAL: Write ONLY in the specified language. Never mix languages. If instructed to write in Hebrew, every word must be in Hebrew (except proper nouns like company names).

Respond ONLY with valid JSON:
{{
  "summary": "...",
  "key_points": ["...", "..."],
  "action_items": ["Person - action", "..."],
  "structured_actions": [],
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "participants": [{{"speaker_label": "Speaker 0", "name": "...", "role": "...", "phone": null}}],
  "topics": ["...", "..."]
}}

CALL TRANSCRIPTION:
{transcription_text}
"""

LANGUAGE_INSTRUCTIONS = {
    "auto": "Respond in the same language as the transcription.",
    "he": "חובה לכתוב בעברית בלבד. כל הטקסט ב-JSON חייב להיות בעברית. אסור לערבב עברית ואנגלית.",
    "en": "Respond in English only. All text in the JSON must be in English.",
}

VALID_ACTION_TYPES = frozenset({"calendar_event", "send_email", "send_whatsapp", "reminder", "task"})
VALID_SENTIMENTS = frozenset({"positive", "neutral", "negative", "mixed"})


@dataclass(frozen=True)
class SummaryResult:
    """Immutable summary result."""

    summary_text: str
    key_points: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    participants: list[str] = field(default_factory=list)
    participants_details: list[dict] = field(default_factory=list)
    structured_actions: list[dict] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
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
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        parsed = self._parse_response(raw_text)

        # Extract participants in both legacy format and new detailed format
        raw_participants = parsed.get("participants", [])
        legacy_participants = self._to_legacy_participants(raw_participants)
        participants_details = self._to_participants_details(raw_participants)

        # Validate and filter structured actions
        structured_actions = self._validate_actions(parsed.get("structured_actions", []))

        # Validate sentiment
        sentiment = parsed.get("sentiment", "neutral")
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "neutral"

        return SummaryResult(
            summary_text=parsed.get("summary", raw_text),
            key_points=parsed.get("key_points", []),
            action_items=parsed.get("action_items", []),
            sentiment=sentiment,
            participants=legacy_participants,
            participants_details=participants_details,
            structured_actions=structured_actions,
            topics=parsed.get("topics", []),
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

    def _to_legacy_participants(self, participants: list) -> list[str]:
        """Convert participant dicts to legacy string format for backwards compatibility."""
        result = []
        for p in participants:
            if isinstance(p, str):
                result.append(p)
            elif isinstance(p, dict):
                label = p.get("speaker_label", "Unknown")
                name = p.get("name", "")
                role = p.get("role", "")
                parts = [label]
                if name:
                    parts.append(name)
                if role:
                    parts.append(role)
                result.append(" - ".join(parts))
        return result

    def _to_participants_details(self, participants: list) -> list[dict]:
        """Normalize participant data to structured dicts."""
        result = []
        for p in participants:
            if isinstance(p, dict):
                result.append({
                    "speaker_label": p.get("speaker_label", "Unknown"),
                    "name": p.get("name"),
                    "role": p.get("role"),
                    "phone": p.get("phone"),
                })
            elif isinstance(p, str):
                result.append({
                    "speaker_label": p,
                    "name": None,
                    "role": None,
                    "phone": None,
                })
        return result

    def _validate_actions(self, actions: list) -> list[dict]:
        """Validate and filter structured actions to known types."""
        validated = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_type = action.get("type")
            if action_type not in VALID_ACTION_TYPES:
                logger.warning("Skipping unknown action type: %s", action_type)
                continue
            confidence = action.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)):
                confidence = 0.5
            validated.append({
                "type": action_type,
                "description": action.get("description", ""),
                "details": action.get("details", {}),
                "confidence": max(0.0, min(1.0, float(confidence))),
            })
        return validated
