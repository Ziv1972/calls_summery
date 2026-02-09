"""Input validation utilities."""

import re

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac"}
MAX_FILENAME_LENGTH = 500
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{6,14}$")


def validate_audio_filename(filename: str) -> tuple[bool, str]:
    """Validate audio file name and extension."""
    if not filename:
        return False, "Filename is required"

    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"Filename too long (max {MAX_FILENAME_LENGTH} chars)"

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Allowed: {ALLOWED_AUDIO_EXTENSIONS}"

    return True, ""


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_REGEX.match(email))


def validate_phone_number(phone: str) -> bool:
    """Validate international phone number format."""
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    return bool(PHONE_REGEX.match(cleaned))


def validate_language_code(code: str) -> bool:
    """Validate supported language code."""
    supported = {"auto", "en", "he", "ar", "fr", "de", "es", "ru", "zh", "ja"}
    return code.lower() in supported
