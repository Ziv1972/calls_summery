"""Twilio WhatsApp service for summary delivery (Phase 2)."""

import logging
from dataclasses import dataclass

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WhatsAppResult:
    """Immutable WhatsApp send result."""

    success: bool
    message_sid: str | None = None
    error: str | None = None


class WhatsAppService:
    """Twilio WhatsApp delivery service."""

    def __init__(self):
        settings = get_settings()
        self._account_sid = settings.twilio_account_sid
        self._auth_token = settings.twilio_auth_token
        self._from_number = settings.twilio_whatsapp_number
        self._client = None

        if self._account_sid and self._auth_token:
            try:
                from twilio.rest import Client

                self._client = Client(self._account_sid, self._auth_token)
            except ImportError:
                logger.warning("Twilio package not installed. WhatsApp disabled.")

    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return self._client is not None and self._from_number is not None

    def send_summary(
        self,
        to_number: str,
        call_filename: str,
        summary_text: str,
        key_points: list[str] | None = None,
        action_items: list[str] | None = None,
    ) -> WhatsAppResult:
        """Send call summary via WhatsApp."""
        if not self.is_configured:
            return WhatsAppResult(success=False, error="WhatsApp service not configured")

        body = self._format_message(
            call_filename=call_filename,
            summary_text=summary_text,
            key_points=key_points or [],
            action_items=action_items or [],
        )

        try:
            message = self._client.messages.create(
                from_=f"whatsapp:{self._from_number}",
                to=f"whatsapp:{to_number}",
                body=body,
            )
            logger.info("WhatsApp sent to %s (sid=%s)", to_number, message.sid)
            return WhatsAppResult(success=True, message_sid=message.sid)
        except Exception as e:
            logger.error("Failed to send WhatsApp to %s: %s", to_number, e)
            return WhatsAppResult(success=False, error=str(e))

    def _format_message(
        self,
        call_filename: str,
        summary_text: str,
        key_points: list[str],
        action_items: list[str],
    ) -> str:
        """Format summary for WhatsApp (plain text, max 1600 chars)."""
        parts = [f"*Call Summary: {call_filename}*\n\n{summary_text}"]

        if key_points:
            points = "\n".join(f"- {p}" for p in key_points)
            parts.append(f"\n\n*Key Points:*\n{points}")

        if action_items:
            items = "\n".join(f"- {a}" for a in action_items)
            parts.append(f"\n\n*Action Items:*\n{items}")

        message = "".join(parts)

        # WhatsApp has a 1600 char limit
        if len(message) > 1580:
            message = message[:1577] + "..."

        return message
