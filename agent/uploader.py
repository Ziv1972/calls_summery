"""S3 uploader for the local agent."""

import logging
import os
import urllib.parse
import uuid

import boto3
from botocore.exceptions import ClientError

from agent.config import AWS_ACCESS_KEY_ID, AWS_REGION, AWS_SECRET_ACCESS_KEY, S3_BUCKET

logger = logging.getLogger(__name__)

AUDIO_CONTENT_TYPES = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/x-m4a",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
}


def upload_file_to_s3(file_path: str) -> dict | None:
    """Upload a local file to S3. Returns metadata dict or None on failure."""
    if not os.path.exists(file_path):
        logger.error("File not found: %s", file_path)
        return None

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    content_type = AUDIO_CONTENT_TYPES.get(ext, "application/octet-stream")
    s3_key = f"calls/{uuid.uuid4()}{ext}"

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    try:
        file_size = os.path.getsize(file_path)

        s3_client.upload_file(
            file_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ContentType": content_type,
                "Metadata": {
                    "original_filename": urllib.parse.quote(filename, safe=""),
                },
            },
        )

        logger.info("Uploaded %s -> s3://%s/%s (%d bytes)", filename, S3_BUCKET, s3_key, file_size)

        return {
            "bucket": S3_BUCKET,
            "key": s3_key,
            "size": file_size,
            "content_type": content_type,
            "original_filename": filename,
        }

    except ClientError as e:
        logger.error("S3 upload failed for %s: %s", filename, e)
        return None
