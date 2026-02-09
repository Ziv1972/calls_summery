"""Formatting utilities for summaries and display."""


def format_duration(seconds: float | None) -> str:
    """Format seconds into human-readable duration."""
    if seconds is None or seconds <= 0:
        return "Unknown"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes == 0:
        return f"{remaining_seconds}s"
    return f"{minutes}m {remaining_seconds}s"


def format_file_size(bytes_count: int) -> str:
    """Format bytes into human-readable size."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f} MB"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_status_badge(status: str) -> str:
    """Return emoji indicator for status (for Streamlit display)."""
    status_map = {
        "uploaded": "📤 Uploaded",
        "transcribing": "🔄 Transcribing",
        "transcribed": "📝 Transcribed",
        "summarizing": "🤖 Summarizing",
        "completed": "✅ Completed",
        "failed": "❌ Failed",
        "pending": "⏳ Pending",
        "processing": "🔄 Processing",
        "sent": "📨 Sent",
        "delivered": "✅ Delivered",
    }
    return status_map.get(status, status)
