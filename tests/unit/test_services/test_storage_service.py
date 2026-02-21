"""Tests for S3 storage service."""

import io
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.services.storage_service import PresignedPutResult, PresignedUrlResult, StorageService, UploadResult


class TestUploadResult:
    """Test UploadResult immutable dataclass."""

    def test_create_upload_result(self):
        result = UploadResult(s3_key="calls/abc.mp3", bucket="test", file_size=1024, content_type="audio/mpeg")
        assert result.s3_key == "calls/abc.mp3"
        assert result.bucket == "test"
        assert result.file_size == 1024
        assert result.content_type == "audio/mpeg"

    def test_upload_result_is_immutable(self):
        result = UploadResult(s3_key="k", bucket="b", file_size=1, content_type="audio/mpeg")
        with pytest.raises(AttributeError):
            result.s3_key = "new"


class TestPresignedUrlResult:
    """Test PresignedUrlResult immutable dataclass."""

    def test_create_presigned_url_result(self):
        result = PresignedUrlResult(url="https://s3.amazonaws.com/test", expires_in=3600)
        assert result.url == "https://s3.amazonaws.com/test"
        assert result.expires_in == 3600

    def test_presigned_url_result_is_immutable(self):
        result = PresignedUrlResult(url="u", expires_in=60)
        with pytest.raises(AttributeError):
            result.url = "new"


class TestPresignedPutResult:
    """Test PresignedPutResult immutable dataclass."""

    def test_create_presigned_put_result(self):
        result = PresignedPutResult(
            upload_url="https://s3.amazonaws.com/put",
            s3_key="calls/uuid.m4a",
            bucket="test-bucket",
            expires_in=900,
        )
        assert result.upload_url == "https://s3.amazonaws.com/put"
        assert result.s3_key == "calls/uuid.m4a"
        assert result.bucket == "test-bucket"
        assert result.expires_in == 900

    def test_presigned_put_result_is_immutable(self):
        result = PresignedPutResult(upload_url="u", s3_key="k", bucket="b", expires_in=60)
        with pytest.raises(AttributeError):
            result.upload_url = "new"


class TestStorageService:
    """Test StorageService with mocked S3."""

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_upload_file_success(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="test-bucket",
            aws_access_key_id="key",
            aws_secret_access_key="secret",
            aws_region="us-east-1",
        )
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        file_data = io.BytesIO(b"fake audio data")
        result = svc.upload_file(file_data, "test.mp3", "audio/mpeg")

        assert isinstance(result, UploadResult)
        assert result.bucket == "test-bucket"
        assert result.file_size == 15
        assert result.content_type == "audio/mpeg"
        assert result.s3_key.startswith("calls/")
        assert result.s3_key.endswith(".mp3")
        mock_client.put_object.assert_called_once()

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_upload_file_s3_error(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal"}}, "PutObject"
        )
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        with pytest.raises(ClientError):
            svc.upload_file(io.BytesIO(b"data"), "test.mp3", "audio/mpeg")

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_generate_presigned_url(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://presigned.url"
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        result = svc.generate_presigned_url("calls/test.mp3", expires_in=7200)

        assert isinstance(result, PresignedUrlResult)
        assert result.url == "https://presigned.url"
        assert result.expires_in == 7200

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_delete_file_success(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        assert svc.delete_file("calls/test.mp3") is True
        mock_client.delete_object.assert_called_once()

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_delete_file_failure(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "DeleteObject"
        )
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        assert svc.delete_file("calls/missing.mp3") is False

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_generate_presigned_put_url(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="test-bucket", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://presigned-put.url"
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        result = svc.generate_presigned_put_url("test.m4a", "audio/x-m4a", expires_in=900)

        assert isinstance(result, PresignedPutResult)
        assert result.upload_url == "https://presigned-put.url"
        assert result.bucket == "test-bucket"
        assert result.expires_in == 900
        assert result.s3_key.startswith("calls/")
        assert result.s3_key.endswith(".m4a")
        mock_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "test-bucket",
                "Key": result.s3_key,
                "ContentType": "audio/x-m4a",
                "Metadata": {"original_filename": "test.m4a"},
            },
            ExpiresIn=900,
        )

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_generate_presigned_put_url_s3_error(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal"}}, "PutObject"
        )
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        with pytest.raises(ClientError):
            svc.generate_presigned_put_url("test.mp3", "audio/mpeg")

    @patch("src.services.storage_service.boto3")
    @patch("src.services.storage_service.get_settings")
    def test_generate_presigned_put_url_no_extension(self, mock_settings, mock_boto3):
        mock_settings.return_value = MagicMock(
            s3_bucket_name="b", aws_access_key_id="k",
            aws_secret_access_key="s", aws_region="r",
        )
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://url"
        mock_boto3.client.return_value = mock_client

        svc = StorageService()
        result = svc.generate_presigned_put_url("noext", "audio/mpeg")
        assert result.s3_key.endswith(".mp3")
