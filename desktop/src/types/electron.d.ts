/** Type declarations for the electron preload bridge. */

interface ElectronBridge {
  settings: {
    get: () => Promise<Record<string, unknown>>;
    set: (updates: Record<string, unknown>) => Promise<Record<string, unknown>>;
  };
  dialogs: {
    openFolder: () => Promise<string | null>;
  };
  watcher: {
    start: (config: Record<string, unknown>) => Promise<boolean>;
    stop: () => Promise<boolean>;
    status: () => Promise<boolean>;
  };
  chat: {
    send: (
      messages: Array<{ role: string; content: string }>,
      systemPrompt: string,
    ) => Promise<string>;
  };
  notifications: {
    show: (title: string, body: string) => void;
    uploadEvent: (event: string, filename: string, callId?: string) => void;
  };
  on: (channel: string, callback: (...args: unknown[]) => void) => void;
  off: (channel: string, callback: (...args: unknown[]) => void) => void;
}

declare global {
  interface Window {
    electron: ElectronBridge;
  }
}

export {};
