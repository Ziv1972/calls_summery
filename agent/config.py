"""Local agent configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (agent runs standalone)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# Folder to watch for new call recordings
# Android: "/storage/emulated/0/Recordings/Call"
# Windows: "C:/Users/YourName/CallRecordings"
WATCH_FOLDER = os.environ.get("WATCH_FOLDER", "C:/Users/zivre/CallRecordings")

# API endpoint for triggering processing
API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:8001/api/webhooks/s3-upload")

# AWS S3 settings (loaded from .env)
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "amzn-callsummery")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-north-1")

# Agent behavior
AUTO_UPLOAD_ENABLED = os.environ.get("AUTO_UPLOAD", "true").lower() == "true"
WATCH_INTERVAL_SECONDS = int(os.environ.get("WATCH_INTERVAL", "5"))
SETTLE_TIME_SECONDS = int(os.environ.get("SETTLE_TIME", "5"))

# Supported audio extensions
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac"}
