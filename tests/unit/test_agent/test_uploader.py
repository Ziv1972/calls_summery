"""Tests for the local agent S3 uploader."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from agent.uploader import AUDIO_CONTENT_TYPES, upload_file_to_s3


class TestAudioContentTypes:
    """Test AUDIO_CONTENT_TYPES mapping."""

    def test_mp3_content_type(self):
        assert AUDIO_CONTENT_TYPES[".mp3"] == "audio/mpeg"

    def test_wav_content_type(self):
        assert AUDIO_CONTENT_TYPES[".wav"] == "audio/wav"

    def test_m4a_content_type(self):
        assert AUDIO_CONTENT_TYPES[".m4a"] == "audio/x-m4a"

    def test_all_common_formats(self):
        expected = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm", ".flac"}
        assert set(AUDIO_CONTENT_TYPES.keys()) == expected


class TestUploadFileToS3:
    """Test upload_file_to_s3 function."""

    def test_file_not_found(self):
        result = upload_file_to_s3("/nonexistent/path/file.mp3")
        assert result is None

    @patch("agent.uploader.boto3")
    def test_upload_success(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            result = upload_file_to_s3(temp_path)

            assert result is not None
            assert result["content_type"] == "audio/mpeg"
            assert result["size"] == 15
            assert result["key"].startswith("calls/")
            assert result["key"].endswith(".mp3")
            assert result["original_filename"] == os.path.basename(temp_path)
            mock_client.upload_file.assert_called_once()
        finally:
            os.unlink(temp_path)

    @patch("agent.uploader.boto3")
    def test_upload_s3_error(self, mock_boto3):
        mock_client = MagicMock()
        mock_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "UploadFile"
        )
        mock_boto3.client.return_value = mock_client

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"data")
            temp_path = f.name

        try:
            result = upload_file_to_s3(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    @patch("agent.uploader.boto3")
    def test_upload_unknown_extension(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"data")
            temp_path = f.name

        try:
            result = upload_file_to_s3(temp_path)
            assert result is not None
            assert result["content_type"] == "application/octet-stream"
        finally:
            os.unlink(temp_path)
