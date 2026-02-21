"""S3 storage service for audio file management."""

import logging
import uuid
from dataclasses import dataclass
from typing import BinaryIO
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadResult:
    """Immutable S3 upload result."""

    s3_key: str
    bucket: str
    file_size: int
    content_type: str


@dataclass(frozen=True)
class PresignedUrlResult:
    """Immutable presigned URL result."""

    url: str
    expires_in: int


@dataclass(frozen=True)
class PresignedPutResult:
    """Immutable presigned PUT URL result for client-side uploads."""

    upload_url: str
    s3_key: str
    bucket: str
    expires_in: int


class StorageService:
    """S3 storage service for audio files."""

    def __init__(self):
        settings = get_settings()
        self._bucket = settings.s3_bucket_name
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    def upload_file(
        self,
        file_data: BinaryIO,
        original_filename: str,
        content_type: str,
    ) -> UploadResult:
        """Upload audio file to S3. Returns immutable result."""
        file_ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "mp3"
        s3_key = f"calls/{uuid.uuid4()}.{file_ext}"

        file_data.seek(0)
        content = file_data.read()
        file_size = len(content)
        file_data.seek(0)

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                Metadata={"original_filename": quote(original_filename)},
            )
        except ClientError as e:
            logger.error("S3 upload failed: %s", e)
            raise

        logger.info("Uploaded %s to s3://%s/%s (%d bytes)", original_filename, self._bucket, s3_key, file_size)

        return UploadResult(
            s3_key=s3_key,
            bucket=self._bucket,
            file_size=file_size,
            content_type=content_type,
        )

    def generate_presigned_url(
        self, s3_key: str, expires_in: int = 3600
    ) -> PresignedUrlResult:
        """Generate a time-limited presigned URL for file access."""
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": s3_key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error("Failed to generate presigned URL: %s", e)
            raise

        return PresignedUrlResult(url=url, expires_in=expires_in)

    def generate_presigned_put_url(
        self,
        original_filename: str,
        content_type: str,
        expires_in: int = 900,
    ) -> PresignedPutResult:
        """Generate a time-limited presigned PUT URL for client-side upload.

        Used by mobile apps that cannot embed AWS credentials.
        Returns the upload URL, generated S3 key, and bucket.
        """
        file_ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "mp3"
        s3_key = f"calls/{uuid.uuid4()}.{file_ext}"

        try:
            url = self._client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error("Failed to generate presigned PUT URL: %s", e)
            raise

        logger.info("Generated presigned PUT URL for %s -> s3://%s/%s", original_filename, self._bucket, s3_key)

        return PresignedPutResult(
            upload_url=url,
            s3_key=s3_key,
            bucket=self._bucket,
            expires_in=expires_in,
        )

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            logger.info("Deleted s3://%s/%s", self._bucket, s3_key)
            return True
        except ClientError as e:
            logger.error("Failed to delete from S3: %s", e)
            return False
