/** Folder watcher - monitors a directory for new audio files and auto-uploads. */

import * as chokidar from "chokidar";
import * as path from "path";
import { BrowserWindow } from "electron";
import { AUDIO_EXTENSIONS, uploadToS3, notifyBackend } from "./uploader";
import type { UploaderConfig, WebhookConfig } from "./uploader";

const SETTLE_TIME_MS = 5_000;

interface WatcherConfig {
  readonly watchFolder: string;
  readonly s3: UploaderConfig;
  readonly webhook: WebhookConfig;
}

let watcher: chokidar.FSWatcher | null = null;
const processed = new Set<string>();

function isAudioFile(filePath: string): boolean {
  const ext = path.extname(filePath).toLowerCase();
  return AUDIO_EXTENSIONS.has(ext);
}

function notifyRenderer(event: string, data: unknown): void {
  const windows = BrowserWindow.getAllWindows();
  for (const win of windows) {
    win.webContents.send(event, data);
  }
}

function isWithinWatchFolder(filePath: string, watchFolder: string): boolean {
  const resolved = path.resolve(filePath);
  const watched = path.resolve(watchFolder);
  return resolved.startsWith(watched + path.sep) || resolved === watched;
}

async function handleNewFile(filePath: string, config: WatcherConfig): Promise<void> {
  if (processed.has(filePath)) return;
  if (!isAudioFile(filePath)) return;
  if (!isWithinWatchFolder(filePath, config.watchFolder)) {
    console.warn(`[watcher] Rejecting file outside watch folder: ${filePath}`);
    return;
  }

  processed.add(filePath);
  const filename = path.basename(filePath);
  console.log(`[watcher] New audio detected: ${filename}, waiting ${SETTLE_TIME_MS}ms to settle...`);

  notifyRenderer("upload:started", { filename, path: filePath });

  // Wait for file to finish writing
  await new Promise((resolve) => setTimeout(resolve, SETTLE_TIME_MS));

  const result = await uploadToS3(filePath, config.s3);
  if (!result) {
    processed.delete(filePath);
    notifyRenderer("upload:failed", { filename, error: "S3 upload failed" });
    return;
  }

  notifyRenderer("upload:uploaded", { filename, key: result.key });

  const callId = await notifyBackend(result, config.webhook);
  if (callId) {
    notifyRenderer("upload:processing", { filename, callId });
  } else {
    notifyRenderer("upload:webhook-failed", { filename, key: result.key });
  }
}

export function startWatcher(config: WatcherConfig): void {
  if (watcher) {
    console.log("[watcher] Already running, stopping first...");
    stopWatcher();
  }

  console.log(`[watcher] Watching folder: ${config.watchFolder}`);

  watcher = chokidar.watch(config.watchFolder, {
    ignoreInitial: true,
    persistent: true,
    awaitWriteFinish: {
      stabilityThreshold: SETTLE_TIME_MS,
      pollInterval: 500,
    },
  });

  watcher.on("add", (filePath: string) => {
    handleNewFile(filePath, config).catch((err) => {
      console.error(`[watcher] Error processing ${filePath}:`, err);
    });
  });

  // Handle file renames/moves (important for Syncthing)
  watcher.on("change", (filePath: string) => {
    if (!processed.has(filePath) && isAudioFile(filePath)) {
      handleNewFile(filePath, config).catch((err) => {
        console.error(`[watcher] Error processing moved file ${filePath}:`, err);
      });
    }
  });

  watcher.on("error", (err) => {
    console.error("[watcher] Error:", err);
  });

  console.log("[watcher] Started");
}

export function stopWatcher(): void {
  if (watcher) {
    watcher.close().catch((err) => console.error("[watcher] Close error:", err));
    watcher = null;
    processed.clear();
    console.log("[watcher] Stopped");
  }
}

export function isWatcherRunning(): boolean {
  return watcher !== null;
}
