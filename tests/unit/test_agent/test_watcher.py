"""Tests for the local agent file watcher."""

from unittest.mock import MagicMock, patch

import pytest

from agent.watcher import CallRecordingHandler


class TestCallRecordingHandler:
    """Test CallRecordingHandler event handling."""

    def test_ignores_directories(self):
        handler = CallRecordingHandler()
        event = MagicMock()
        event.is_directory = True
        event.src_path = "/some/dir"

        # Should not raise or process
        handler.on_created(event)
        assert len(handler._processed) == 0

    def test_ignores_non_audio_files(self):
        handler = CallRecordingHandler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/file.txt"

        handler.on_created(event)
        assert len(handler._processed) == 0

    def test_ignores_already_processed(self):
        handler = CallRecordingHandler()
        handler._processed.add("/some/file.mp3")

        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/file.mp3"

        handler.on_created(event)
        # Should still be just 1 (no re-processing)
        assert len(handler._processed) == 1

    @patch("agent.watcher.AUTO_UPLOAD_ENABLED", False)
    @patch("agent.watcher.time")
    def test_skips_when_auto_upload_disabled(self, mock_time):
        handler = CallRecordingHandler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/recording.mp3"

        handler.on_created(event)
        # File should NOT be processed when disabled
        assert "/some/recording.mp3" not in handler._processed

    @patch("agent.watcher.upload_file_to_s3")
    @patch("agent.watcher.AUTO_UPLOAD_ENABLED", True)
    @patch("agent.watcher.SETTLE_TIME_SECONDS", 0)
    @patch("agent.watcher.time")
    def test_processes_audio_file(self, mock_time, mock_upload):
        mock_upload.return_value = None  # Simulate upload failure

        handler = CallRecordingHandler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/call.m4a"

        handler.on_created(event)
        mock_upload.assert_called_once_with("/some/call.m4a")
        # On failure, file is removed from processed so it can retry
        assert "/some/call.m4a" not in handler._processed

    @patch("agent.watcher.httpx")
    @patch("agent.watcher.upload_file_to_s3")
    @patch("agent.watcher.AUTO_UPLOAD_ENABLED", True)
    @patch("agent.watcher.SETTLE_TIME_SECONDS", 0)
    @patch("agent.watcher.time")
    def test_processes_and_notifies_api(self, mock_time, mock_upload, mock_httpx):
        mock_upload.return_value = {
            "bucket": "test-bucket",
            "key": "calls/abc.mp3",
            "size": 1024,
            "content_type": "audio/mpeg",
            "original_filename": "call.mp3",
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"call_id": "123"}
        mock_httpx.post.return_value = mock_response

        handler = CallRecordingHandler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/call.mp3"

        handler.on_created(event)
        assert "/some/call.mp3" in handler._processed
        mock_httpx.post.assert_called_once()

    def test_supported_extensions(self):
        handler = CallRecordingHandler()
        supported = [".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac"]
        for ext in supported:
            event = MagicMock()
            event.is_directory = False
            event.src_path = f"/test/file{ext}"
            # Reset processed
            handler._processed.clear()
            # Should not raise
            with patch("agent.watcher.AUTO_UPLOAD_ENABLED", False):
                handler.on_created(event)
