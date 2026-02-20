"""Action service - generate deep links and execution payloads from structured actions."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActionLink:
    """Immutable action with generated deep links."""

    type: str
    description: str
    details: dict = field(default_factory=dict)
    confidence: float = 0.5
    deep_link: str | None = None
    link_type: str = "url"


def generate_action_links(structured_actions: list[dict]) -> list[ActionLink]:
    """Generate deep links for each structured action."""
    return [_build_action_link(action) for action in structured_actions]


def _build_action_link(action: dict) -> ActionLink:
    """Build an ActionLink with appropriate deep link for the action type."""
    action_type = action.get("type", "")
    description = action.get("description", "")
    details = action.get("details", {})
    confidence = action.get("confidence", 0.5)

    deep_link = None
    link_type = "url"

    if action_type == "calendar_event":
        deep_link = _calendar_deep_link(details)
    elif action_type == "send_email":
        deep_link = _email_deep_link(details)
    elif action_type == "send_whatsapp":
        deep_link = _whatsapp_deep_link(details)
    elif action_type == "reminder":
        link_type = "local"
    elif action_type == "task":
        link_type = "local"

    return ActionLink(
        type=action_type,
        description=description,
        details=details,
        confidence=confidence,
        deep_link=deep_link,
        link_type=link_type,
    )


def _calendar_deep_link(details: dict) -> str | None:
    """Generate Google Calendar deep link."""
    title = details.get("title", "Event")
    date = details.get("date", "")
    time_str = details.get("time", "")
    duration = details.get("duration_minutes", 60)

    if not date:
        return None

    # Format: YYYYMMDDTHHMMSS
    try:
        if time_str:
            dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M")
        else:
            dt = datetime.strptime(date, "%Y-%m-%d")
            dt = dt.replace(hour=9, minute=0)

        start = dt.strftime("%Y%m%dT%H%M%S")

        from datetime import timedelta
        end_dt = dt + timedelta(minutes=duration)
        end = end_dt.strftime("%Y%m%dT%H%M%S")

        encoded_title = quote(title)
        participants = details.get("participants", [])
        add_guests = ",".join(participants) if participants else ""

        link = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={encoded_title}&dates={start}/{end}"
        )
        if add_guests:
            link += f"&add={quote(add_guests)}"
        return link
    except (ValueError, TypeError):
        logger.warning("Failed to parse calendar event date: %s %s", date, time_str)
        return None


def _email_deep_link(details: dict) -> str | None:
    """Generate mailto: deep link."""
    to_email = details.get("to_email", "")
    subject = details.get("subject", "")
    body_outline = details.get("body_outline", "")

    if not to_email and not subject:
        return None

    link = f"mailto:{quote(to_email)}"
    params = []
    if subject:
        params.append(f"subject={quote(subject)}")
    if body_outline:
        params.append(f"body={quote(body_outline)}")
    if params:
        link += "?" + "&".join(params)
    return link


def _whatsapp_deep_link(details: dict) -> str | None:
    """Generate WhatsApp deep link."""
    phone = details.get("phone", "")
    message = details.get("message_outline", "") or details.get("message", "")

    if not phone:
        return None

    # Strip non-digits except leading +
    clean_phone = phone.lstrip("+")
    import re
    clean_phone = re.sub(r"[^\d]", "", clean_phone)

    link = f"https://wa.me/{clean_phone}"
    if message:
        link += f"?text={quote(message)}"
    return link
