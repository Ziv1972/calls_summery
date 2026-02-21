/** S3 uploader - uploads audio files to S3 and notifies the backend. */

import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import * as fs from "fs";
import * as path from "path";
import { randomUUID } from "crypto";

const AUDIO_CONTENT_TYPES: Record<string, string> = {
  ".mp3": "audio/mpeg",
  ".mp4": "audio/mp4",
  ".m4a": "audio/x-m4a",
  ".wav": "audio/wav",
  ".ogg": "audio/ogg",
  ".webm": "audio/webm",
  ".flac": "audio/flac",
};

export const AUDIO_EXTENSIONS = new Set(Object.keys(AUDIO_CONTENT_TYPES));

export interface UploadResult {
  readonly bucket: string;
  readonly key: string;
  readonly size: number;
  readonly contentType: string;
  readonly originalFilename: string;
}

export interface UploaderConfig {
  readonly bucket: string;
  readonly region: string;
  readonly accessKeyId: string;
  readonly secretAccessKey: string;
}

function createS3Client(config: UploaderConfig): S3Client {
  return new S3Client({
    region: config.region,
    credentials: {
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
    },
  });
}

export async function uploadToS3(
  filePath: string,
  config: UploaderConfig,
): Promise<UploadResult | null> {
  if (!fs.existsSync(filePath)) {
    console.error(`[uploader] File not found: ${filePath}`);
    return null;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = AUDIO_CONTENT_TYPES[ext] ?? "application/octet-stream";
  const originalFilename = path.basename(filePath);
  const s3Key = `calls/${randomUUID()}${ext}`;

  const fileBuffer = fs.readFileSync(filePath);
  const size = fileBuffer.length;

  const client = createS3Client(config);

  try {
    await client.send(
      new PutObjectCommand({
        Bucket: config.bucket,
        Key: s3Key,
        Body: fileBuffer,
        ContentType: contentType,
        Metadata: {
          original_filename: encodeURIComponent(originalFilename),
        },
      }),
    );

    console.log(`[uploader] Uploaded ${originalFilename} -> s3://${config.bucket}/${s3Key}`);

    return {
      bucket: config.bucket,
      key: s3Key,
      size,
      contentType,
      originalFilename,
    };
  } catch (err) {
    console.error(`[uploader] S3 upload failed for ${originalFilename}:`, err);
    return null;
  }
}

export interface WebhookConfig {
  readonly apiUrl: string;
  readonly token: string;
}

export async function notifyBackend(
  upload: UploadResult,
  webhook: WebhookConfig,
): Promise<string | null> {
  const url = `${webhook.apiUrl}/api/webhooks/s3-upload`;
  const body = {
    bucket: upload.bucket,
    key: upload.key,
    size: upload.size,
    content_type: upload.contentType,
    original_filename: upload.originalFilename,
  };

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(webhook.token ? { Authorization: `Bearer ${webhook.token}` } : {}),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });

    if (!response.ok) {
      console.error(`[uploader] Webhook returned ${response.status}: ${response.statusText}`);
      return null;
    }

    const data = (await response.json()) as { data?: { call_id?: string } };
    const callId = data?.data?.call_id ?? null;
    console.log(`[uploader] Backend notified for ${upload.originalFilename} (call_id=${callId})`);
    return callId;
  } catch (err) {
    console.error(`[uploader] Webhook failed for ${upload.originalFilename}:`, err);
    return null;
  }
}
