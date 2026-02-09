"""Audio file utilities."""

AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/x-m4a",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
}


def get_content_type(filename: str) -> str:
    """Get MIME type from filename extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return AUDIO_MIME_TYPES.get(ext, "application/octet-stream")


def is_audio_file(filename: str) -> bool:
    """Check if filename has a recognized audio extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in AUDIO_MIME_TYPES
