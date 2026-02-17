"""File system watcher - monitors a folder for new call recordings."""

import logging
import os
import sys
import time

import httpx
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.config import (
    API_ENDPOINT,
    API_KEY,
    AUDIO_EXTENSIONS,
    AUTO_UPLOAD_ENABLED,
    SETTLE_TIME_SECONDS,
    WATCH_FOLDER,
)
from agent.uploader import upload_file_to_s3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agent.watcher")


class CallRecordingHandler(FileSystemEventHandler):
    """Handles new audio files detected in the watch folder."""

    def __init__(self):
        self._processed = set()

    def on_created(self, event):
        """Called when a new file is created."""
        if event.is_directory:
            return
        self._handle_new_file(event.src_path)

    def on_moved(self, event):
        """Called when a file is renamed/moved (Syncthing uses rename)."""
        if event.is_directory:
            return
        self._handle_new_file(event.dest_path)

    def _handle_new_file(self, file_path: str):
        """Process a newly detected audio file."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext not in AUDIO_EXTENSIONS:
            return

        if file_path in self._processed:
            return

        logger.info("New audio file detected: %s", os.path.basename(file_path))

        if not AUTO_UPLOAD_ENABLED:
            logger.info("Auto-upload disabled, skipping %s", file_path)
            return

        # Wait for file to be fully written
        logger.info("Waiting %ds for file to settle...", SETTLE_TIME_SECONDS)
        time.sleep(SETTLE_TIME_SECONDS)

        self._process_file(file_path)

    def _process_file(self, file_path: str):
        """Upload file to S3 and notify API."""
        self._processed.add(file_path)

        # Upload to S3
        result = upload_file_to_s3(file_path)
        if result is None:
            logger.error("Failed to upload %s", file_path)
            self._processed.discard(file_path)
            return

        # Notify API to start processing
        try:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

            response = httpx.post(
                API_ENDPOINT,
                json={
                    "bucket": result["bucket"],
                    "key": result["key"],
                    "size": result["size"],
                    "content_type": result["content_type"],
                    "original_filename": result["original_filename"],
                },
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "Processing started for %s (call_id=%s)",
                    result["original_filename"],
                    data.get("call_id"),
                )
            else:
                logger.error("API notification failed: HTTP %s", response.status_code)

        except Exception as e:
            logger.error("Failed to notify API: %s", e)


def scan_existing_files(handler: CallRecordingHandler):
    """Process audio files already present in the watch folder."""
    for filename in os.listdir(WATCH_FOLDER):
        file_path = os.path.join(WATCH_FOLDER, filename)
        if not os.path.isfile(file_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            logger.info("Found existing file: %s", filename)
            handler._handle_new_file(file_path)


def _collect_existing_files():
    """Return set of all audio file paths currently in watch folder."""
    existing = set()
    for filename in os.listdir(WATCH_FOLDER):
        file_path = os.path.join(WATCH_FOLDER, filename)
        if not os.path.isfile(file_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            existing.add(file_path)
    return existing


def main():
    """Run the file watcher."""
    if not os.path.isdir(WATCH_FOLDER):
        logger.error("Watch folder does not exist: %s", WATCH_FOLDER)
        logger.info("Create the folder or set WATCH_FOLDER environment variable")
        sys.exit(1)

    logger.info("Starting call recording watcher")
    logger.info("Watch folder: %s", WATCH_FOLDER)
    logger.info("Auto-upload: %s", "enabled" if AUTO_UPLOAD_ENABLED else "disabled")
    logger.info("API endpoint: %s", API_ENDPOINT)

    handler = CallRecordingHandler()

    if "--scan-existing" in sys.argv:
        logger.info("Scanning existing files in watch folder...")
        scan_existing_files(handler)
    elif "--process-file" in sys.argv:
        # Process a specific file by name pattern
        idx = sys.argv.index("--process-file") + 1
        if idx < len(sys.argv):
            pattern = sys.argv[idx]
            for filename in os.listdir(WATCH_FOLDER):
                if pattern in filename:
                    file_path = os.path.join(WATCH_FOLDER, filename)
                    logger.info("Processing specific file: %s", filename)
                    handler._handle_new_file(file_path)
                    break
            else:
                logger.error("No file matching '%s' found", pattern)
                sys.exit(1)
        else:
            logger.error("--process-file requires a filename pattern")
            sys.exit(1)
    else:
        # Mark all existing files as already processed so only new arrivals trigger
        existing = _collect_existing_files()
        handler._processed = existing
        logger.info("Marked %d existing files as already processed", len(existing))

    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()

    logger.info("Watching for new recordings... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
