/** Preload script - secure IPC bridge between main and renderer. */

import { contextBridge, ipcRenderer } from "electron";

const ALLOWED_RECEIVE_CHANNELS = new Set([
  "navigate",
  "upload:started",
  "upload:uploaded",
  "upload:failed",
  "upload:processing",
  "upload:webhook-failed",
]);

contextBridge.exposeInMainWorld("electron", {
  settings: {
    get: () => ipcRenderer.invoke("settings:get"),
    set: (updates: Record<string, unknown>) =>
      ipcRenderer.invoke("settings:set", updates),
  },
  dialogs: {
    openFolder: () => ipcRenderer.invoke("dialog:openFolder"),
  },
  watcher: {
    start: (config: Record<string, unknown>) =>
      ipcRenderer.invoke("watcher:start", config),
    stop: () => ipcRenderer.invoke("watcher:stop"),
    status: () => ipcRenderer.invoke("watcher:status") as Promise<boolean>,
  },
  chat: {
    send: (
      messages: Array<{ role: string; content: string }>,
      systemPrompt: string,
    ) => ipcRenderer.invoke("chat:send", messages, systemPrompt),
  },
  notifications: {
    show: (title: string, body: string) =>
      ipcRenderer.send("notification:show", { title, body }),
    uploadEvent: (event: string, filename: string, callId?: string) =>
      ipcRenderer.send("upload:notify", { event, filename, callId }),
  },
  on: (channel: string, callback: (...args: unknown[]) => void) => {
    if (!ALLOWED_RECEIVE_CHANNELS.has(channel)) {
      console.warn(`[preload] Blocked subscription to channel: ${channel}`);
      return;
    }
    ipcRenderer.on(channel, (_, ...args) => callback(...args));
  },
  off: (channel: string, callback: (...args: unknown[]) => void) => {
    if (!ALLOWED_RECEIVE_CHANNELS.has(channel)) return;
    ipcRenderer.removeListener(channel, callback);
  },
});
