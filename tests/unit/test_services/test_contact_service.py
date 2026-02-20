"""Tests for contact service - phone extraction and normalization."""

import pytest

from src.services.contact_service import extract_phone_numbers, normalize_phone


class TestNormalizePhone:
    """Test phone number normalization."""

    def test_international_format(self):
        result = normalize_phone("+972-50-123-4567")
        assert result is not None
        assert "972501234567" in result

    def test_strips_spaces_and_dashes(self):
        result = normalize_phone("+972 50 123 4567")
        assert result is not None
        assert " " not in result
        assert "-" not in result

    def test_too_short_returns_none(self):
        assert normalize_phone("123") is None
        assert normalize_phone("12345") is None

    def test_valid_local_number(self):
        result = normalize_phone("050-123-4567")
        assert result is not None
        assert len(result) >= 7

    def test_empty_string(self):
        assert normalize_phone("") is None


class TestExtractPhoneNumbers:
    """Test phone number extraction from participant details."""

    def test_extracts_phones_from_participants(self):
        participants = [
            {"speaker_label": "Speaker 0", "name": "David", "phone": "+972501234567"},
            {"speaker_label": "Speaker 1", "name": "Sarah", "phone": None},
        ]
        phones = extract_phone_numbers(participants)
        assert len(phones) == 1
        assert "972501234567" in phones[0]

    def test_empty_participants(self):
        assert extract_phone_numbers([]) == []

    def test_no_phones(self):
        participants = [
            {"speaker_label": "Speaker 0", "name": "David", "phone": None},
        ]
        assert extract_phone_numbers(participants) == []

    def test_multiple_phones(self):
        participants = [
            {"speaker_label": "Speaker 0", "name": "David", "phone": "+972501234567"},
            {"speaker_label": "Speaker 1", "name": "Sarah", "phone": "+972521234567"},
        ]
        phones = extract_phone_numbers(participants)
        assert len(phones) == 2
