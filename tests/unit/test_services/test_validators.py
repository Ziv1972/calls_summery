"""Tests for validation utilities."""

import pytest

from src.utils.validators import (
    validate_audio_filename,
    validate_email,
    validate_language_code,
    validate_phone_number,
)


class TestValidateAudioFilename:
    def test_valid_mp3(self):
        valid, error = validate_audio_filename("call.mp3")
        assert valid is True
        assert error == ""

    def test_valid_wav(self):
        valid, error = validate_audio_filename("recording.wav")
        assert valid is True

    def test_valid_m4a(self):
        valid, error = validate_audio_filename("call_2024.m4a")
        assert valid is True

    def test_invalid_extension(self):
        valid, error = validate_audio_filename("document.pdf")
        assert valid is False
        assert "Unsupported" in error

    def test_empty_filename(self):
        valid, error = validate_audio_filename("")
        assert valid is False
        assert "required" in error

    def test_too_long_filename(self):
        valid, error = validate_audio_filename("a" * 501 + ".mp3")
        assert valid is False
        assert "too long" in error

    def test_no_extension(self):
        valid, error = validate_audio_filename("noextension")
        assert valid is False


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_valid_email_with_dots(self):
        assert validate_email("first.last@company.co.il") is True

    def test_invalid_email_no_at(self):
        assert validate_email("not-an-email") is False

    def test_invalid_email_no_domain(self):
        assert validate_email("user@") is False

    def test_empty_email(self):
        assert validate_email("") is False


class TestValidatePhoneNumber:
    def test_valid_international(self):
        assert validate_phone_number("+972501234567") is True

    def test_valid_us(self):
        assert validate_phone_number("+12125551234") is True

    def test_invalid_short(self):
        assert validate_phone_number("123") is False

    def test_valid_with_spaces(self):
        assert validate_phone_number("+972 50 123 4567") is True


class TestValidateLanguageCode:
    def test_auto(self):
        assert validate_language_code("auto") is True

    def test_hebrew(self):
        assert validate_language_code("he") is True

    def test_english(self):
        assert validate_language_code("en") is True

    def test_unsupported(self):
        assert validate_language_code("xx") is False

    def test_case_insensitive(self):
        assert validate_language_code("EN") is True
