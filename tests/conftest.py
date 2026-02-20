"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_transcription_text():
    """Sample transcription text for testing."""
    return (
        "Speaker A: Hi, thanks for calling. How can I help you today?\n"
        "Speaker B: Hi, I'm calling about the project deadline. "
        "We need to extend it by two weeks.\n"
        "Speaker A: I understand. Let me check the schedule. "
        "Yes, we can move the deadline to March 15th.\n"
        "Speaker B: Great, that works. Also, can you send me the updated specs?\n"
        "Speaker A: Sure, I'll email those to you by end of day.\n"
        "Speaker B: Perfect. Thanks for your help.\n"
        "Speaker A: You're welcome. Have a great day!"
    )


@pytest.fixture
def sample_call_data():
    """Sample call record data."""
    return {
        "filename": "test-call-001.mp3",
        "original_filename": "Meeting Recording 2024-01-15.mp3",
        "s3_key": "calls/test-uuid-001.mp3",
        "s3_bucket": "calls-summery-test",
        "file_size_bytes": 5242880,
        "content_type": "audio/mpeg",
    }


@pytest.fixture
def sample_summary_json():
    """Sample Claude API summary response."""
    return {
        "summary": "A call about extending the project deadline by two weeks to March 15th.",
        "key_points": [
            "Project deadline extension requested",
            "New deadline set to March 15th",
            "Updated specs to be sent via email",
        ],
        "action_items": [
            "Send updated specs by end of day",
            "Update project timeline to reflect March 15th deadline",
        ],
        "sentiment": "positive",
        "participants": ["Speaker A", "Speaker B"],
    }


@pytest.fixture
def sample_summary_json_v2():
    """Sample Claude API summary response with structured actions."""
    return {
        "summary": "A call about extending the project deadline by two weeks to March 15th.",
        "key_points": [
            "Project deadline extension requested",
            "New deadline set to March 15th",
            "Updated specs to be sent via email",
        ],
        "action_items": [
            "Send updated specs by end of day",
            "Update project timeline to reflect March 15th deadline",
        ],
        "structured_actions": [
            {
                "type": "send_email",
                "description": "Send updated specs to David",
                "details": {
                    "to_name": "David",
                    "to_email": "david@example.com",
                    "subject": "Updated Project Specs",
                    "body_outline": "Attached updated specs as discussed",
                },
                "confidence": 0.9,
            },
            {
                "type": "calendar_event",
                "description": "New deadline March 15th",
                "details": {
                    "title": "Project Deadline",
                    "date": "2026-03-15",
                    "time": "09:00",
                    "duration_minutes": 60,
                },
                "confidence": 0.8,
            },
            {
                "type": "reminder",
                "description": "Follow up on specs delivery",
                "details": {
                    "date": "2026-02-21",
                    "time": "17:00",
                    "note": "Check if specs were sent",
                },
                "confidence": 0.7,
            },
        ],
        "participants": [
            {"speaker_label": "Speaker 0", "name": "David", "role": "Client", "phone": "+972501234567"},
            {"speaker_label": "Speaker 1", "name": None, "role": "Project Manager", "phone": None},
        ],
        "topics": ["project deadline", "specs delivery", "timeline"],
        "sentiment": "positive",
    }
