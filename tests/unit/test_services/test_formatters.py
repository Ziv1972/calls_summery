"""Tests for formatting utilities."""

from src.utils.formatters import format_duration, format_file_size, format_status_badge, truncate_text


class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration(45) == "45s"

    def test_minutes_and_seconds(self):
        assert format_duration(125) == "2m 5s"

    def test_zero(self):
        assert format_duration(0) == "Unknown"

    def test_none(self):
        assert format_duration(None) == "Unknown"

    def test_exact_minute(self):
        assert format_duration(60) == "1m 0s"


class TestFormatFileSize:
    def test_bytes(self):
        assert format_file_size(500) == "500 B"

    def test_kilobytes(self):
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_file_size(5242880) == "5.0 MB"


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello", 200) == "hello"

    def test_long_text_truncated(self):
        result = truncate_text("a" * 300, 200)
        assert len(result) == 200
        assert result.endswith("...")


class TestFormatStatusBadge:
    def test_completed(self):
        assert "Completed" in format_status_badge("completed")

    def test_failed(self):
        assert "Failed" in format_status_badge("failed")

    def test_unknown(self):
        assert format_status_badge("xyz") == "xyz"
