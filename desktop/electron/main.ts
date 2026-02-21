/** Electron main process - window management, tray, IPC, chat. */

import { app, BrowserWindow, ipcMain, Tray, Menu, Notification, dialog, session } from "electron";
import * as path from "path";
import Store from "electron-store";
import Anthropic from "@anthropic-ai/sdk";
import { startWatcher, stopWatcher, isWatcherRunning } from "./watcher";

// electron-store v10 is ESM; cast to work around CJS type resolution
const store = new (Store as unknown as new () => {
  get(key: string, defaultValue?: unknown): unknown;
  set(key: string, value: unknown): void;
})();

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let isQuitting = false;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "Calls Summary",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Detect dev mode: check if Vite dev server is likely running
  const isDev = !app.isPackaged;
  const apiUrl = process.env.VITE_API_URL || "http://localhost:8001";

  // Content Security Policy (relaxed in dev for Vite HMR)
  if (!isDev) {
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          "Content-Security-Policy": [
            `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ${apiUrl}; img-src 'self' data:`,
          ],
        },
      });
    });
  }

  // Load the app
  if (isDev) {
    mainWindow.loadURL("http://localhost:3000");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }

  // Minimize to tray instead of closing
  mainWindow.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });
}

function createTray() {
  tray = new Tray(
    path.join(__dirname, "../public/icons/tray-icon.png")
  );

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open Calls Summary",
      click: () => mainWindow?.show(),
    },
    { type: "separator" },
    {
      label: "Settings",
      click: () => {
        mainWindow?.show();
        mainWindow?.webContents.send("navigate", "/settings");
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip("Calls Summary");
  tray.setContextMenu(contextMenu);
  tray.on("click", () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow?.show();
    }
  });
}

// IPC handlers

// Settings (atomic update to prevent race conditions)
ipcMain.handle("settings:get", () => {
  return store.get("settings", {});
});

ipcMain.handle("settings:set", (_, updates: Record<string, unknown>) => {
  const current = (store.get("settings", {}) as Record<string, unknown>) || {};
  store.set("settings", { ...current, ...updates });
  return store.get("settings");
});

// Dialogs
ipcMain.handle("dialog:openFolder", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  });
  return result.canceled ? null : result.filePaths[0];
});

// Notifications
ipcMain.on("notification:show", (_, { title, body }: { title: string; body: string }) => {
  if (typeof title !== "string" || typeof body !== "string") return;
  new Notification({ title: title.slice(0, 256), body: body.slice(0, 1024) }).show();
});

// AI Chat (runs in main process - API key never exposed to renderer)
ipcMain.handle(
  "chat:send",
  async (
    _,
    messages: Array<{ role: "user" | "assistant"; content: string }>,
    systemPrompt: string,
  ) => {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY not set in environment");
    }

    const anthropic = new Anthropic({ apiKey });
    const response = await anthropic.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1024,
      system: systemPrompt,
      messages,
    });

    return response.content[0].type === "text" ? response.content[0].text : "";
  },
);

// Watcher (auto-upload) with input validation
function isValidWatcherConfig(config: unknown): config is {
  watchFolder: string;
  s3: { bucket: string; region: string; accessKeyId: string; secretAccessKey: string };
  webhook: { apiUrl: string; token: string };
} {
  if (typeof config !== "object" || config === null) return false;
  const c = config as Record<string, unknown>;
  if (typeof c.watchFolder !== "string" || c.watchFolder.length === 0) return false;
  const s3 = c.s3 as Record<string, unknown> | undefined;
  if (!s3 || typeof s3.bucket !== "string" || typeof s3.region !== "string") return false;
  if (typeof s3.accessKeyId !== "string" || typeof s3.secretAccessKey !== "string") return false;
  const wh = c.webhook as Record<string, unknown> | undefined;
  if (!wh || typeof wh.apiUrl !== "string" || typeof wh.token !== "string") return false;
  return true;
}

ipcMain.handle("watcher:start", (_, config: unknown) => {
  if (!isValidWatcherConfig(config)) {
    throw new Error("Invalid watcher configuration");
  }
  startWatcher(config);
  return true;
});

ipcMain.handle("watcher:stop", () => {
  stopWatcher();
  return true;
});

ipcMain.handle("watcher:status", () => {
  return isWatcherRunning();
});

// Upload notifications
ipcMain.on("upload:notify", (_, data: unknown) => {
  if (typeof data !== "object" || data === null) return;
  const d = data as Record<string, unknown>;
  if (typeof d.event !== "string" || typeof d.filename !== "string") return;
  const filename = d.filename.slice(0, 256);

  switch (d.event) {
    case "uploaded":
      new Notification({
        title: "File Uploaded",
        body: `${filename} uploaded successfully. Processing...`,
      }).show();
      break;
    case "processing":
      new Notification({
        title: "Processing Started",
        body: `${filename} is being transcribed and summarized.`,
      }).show();
      break;
    case "failed":
      new Notification({
        title: "Upload Failed",
        body: `Failed to upload ${filename}. Will retry later.`,
      }).show();
      break;
  }
});

// Auto-resume watcher on app launch if it was enabled
function autoStartWatcher() {
  const settings = store.get("settings", {}) as Record<string, unknown>;
  const enabled = settings.autoUploadEnabled as boolean;
  const folder = settings.watchFolder as string;
  if (!enabled || !folder) return;

  const s3Config = {
    bucket: (settings.s3Bucket as string) || "amzn-callsummery",
    region: (settings.s3Region as string) || "eu-north-1",
    accessKeyId: (settings.awsAccessKeyId as string) || "",
    secretAccessKey: (settings.awsSecretAccessKey as string) || "",
  };

  const token = (settings.lastAuthToken as string) || "";
  const apiUrl = (settings.apiUrl as string) || "http://localhost:8001";

  if (!s3Config.accessKeyId) {
    console.log("[auto-start] Skipping watcher: no AWS credentials configured");
    return;
  }

  console.log(`[auto-start] Resuming watcher on ${folder}`);
  startWatcher({
    watchFolder: folder,
    s3: s3Config,
    webhook: { apiUrl, token },
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();
  autoStartWatcher();

  try {
    createTray();
  } catch {
    console.log("Tray icon not found, skipping tray creation");
  }
});

app.on("before-quit", () => {
  isQuitting = true;
  stopWatcher();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
