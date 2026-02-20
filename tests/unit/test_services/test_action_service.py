"""Tests for action service - deep link generation."""

import pytest

from src.services.action_service import ActionLink, generate_action_links


class TestGenerateActionLinks:
    """Test deep link generation from structured actions."""

    def test_calendar_event_deep_link(self):
        """Calendar event should generate Google Calendar URL."""
        actions = [
            {
                "type": "calendar_event",
                "description": "Meeting with David",
                "details": {
                    "title": "Follow-up meeting",
                    "date": "2026-02-25",
                    "time": "14:00",
                    "duration_minutes": 60,
                },
                "confidence": 0.9,
            }
        ]
        links = generate_action_links(actions)

        assert len(links) == 1
        link = links[0]
        assert isinstance(link, ActionLink)
        assert link.type == "calendar_event"
        assert link.deep_link is not None
        assert "calendar.google.com" in link.deep_link
        assert "Follow-up" in link.deep_link
        assert "20260225" in link.deep_link
        assert link.link_type == "url"

    def test_email_deep_link(self):
        """Email action should generate mailto: link."""
        actions = [
            {
                "type": "send_email",
                "description": "Send proposal",
                "details": {
                    "to_email": "david@example.com",
                    "subject": "Project Proposal",
                    "body_outline": "As discussed",
                },
                "confidence": 0.8,
            }
        ]
        links = generate_action_links(actions)

        assert len(links) == 1
        link = links[0]
        assert link.deep_link is not None
        assert link.deep_link.startswith("mailto:")
        assert "david%40example.com" in link.deep_link or "david@example.com" in link.deep_link
        assert "Project" in link.deep_link

    def test_whatsapp_deep_link(self):
        """WhatsApp action should generate wa.me link."""
        actions = [
            {
                "type": "send_whatsapp",
                "description": "Send contract",
                "details": {
                    "phone": "+972-50-123-4567",
                    "message_outline": "Sending contract",
                },
                "confidence": 0.7,
            }
        ]
        links = generate_action_links(actions)

        assert len(links) == 1
        link = links[0]
        assert link.deep_link is not None
        assert "wa.me" in link.deep_link
        assert "9725012345" in link.deep_link

    def test_reminder_has_no_deep_link(self):
        """Reminder should be marked as local with no deep link."""
        actions = [
            {
                "type": "reminder",
                "description": "Follow up Friday",
                "details": {"date": "2026-02-28", "time": "09:00"},
                "confidence": 0.8,
            }
        ]
        links = generate_action_links(actions)

        assert len(links) == 1
        assert links[0].deep_link is None
        assert links[0].link_type == "local"

    def test_task_has_no_deep_link(self):
        """Task should be marked as local with no deep link."""
        actions = [
            {
                "type": "task",
                "description": "Prepare budget",
                "details": {"title": "Budget", "due_date": "2026-02-24"},
                "confidence": 0.9,
            }
        ]
        links = generate_action_links(actions)

        assert len(links) == 1
        assert links[0].deep_link is None
        assert links[0].link_type == "local"

    def test_empty_actions_list(self):
        """Empty list should return empty results."""
        links = generate_action_links([])
        assert links == []

    def test_calendar_without_date_returns_none(self):
        """Calendar event without date should have no deep link."""
        actions = [
            {
                "type": "calendar_event",
                "description": "Some meeting",
                "details": {"title": "Meeting"},
                "confidence": 0.5,
            }
        ]
        links = generate_action_links(actions)
        assert links[0].deep_link is None

    def test_multiple_actions(self):
        """Should handle multiple actions of different types."""
        actions = [
            {"type": "send_email", "description": "Email", "details": {"to_email": "a@b.com", "subject": "Hi"}, "confidence": 0.9},
            {"type": "send_whatsapp", "description": "WhatsApp", "details": {"phone": "+1234567890"}, "confidence": 0.8},
            {"type": "task", "description": "Task", "details": {}, "confidence": 0.7},
        ]
        links = generate_action_links(actions)
        assert len(links) == 3
        assert links[0].type == "send_email"
        assert links[1].type == "send_whatsapp"
        assert links[2].type == "task"
