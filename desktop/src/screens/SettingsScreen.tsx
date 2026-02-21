/** Settings screen - language, notifications, auto-upload, and local preferences. */

import { useEffect, useState } from "react";
import apiClient from "../api/client";

export function SettingsScreen() {
  const [language, setLanguage] = useState("auto");
  const [notifyOnComplete, setNotifyOnComplete] = useState(true);
  const [notificationMethod, setNotificationMethod] = useState("email");
  const [emailRecipient, setEmailRecipient] = useState("");
  const [whatsappRecipient, setWhatsappRecipient] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Auto-upload local settings
  const [watchFolder, setWatchFolder] = useState("");
  const [autoUploadEnabled, setAutoUploadEnabled] = useState(false);
  const [watcherRunning, setWatcherRunning] = useState(false);

  useEffect(() => {
    loadSettings();
    loadLocalSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const { data } = await apiClient.get("/settings/");
      const s = data.data;
      setLanguage(s.summary_language || "auto");
      setNotifyOnComplete(s.notify_on_complete ?? true);
      setNotificationMethod(s.notification_method || "email");
      setEmailRecipient(s.email_recipient || "");
      setWhatsappRecipient(s.whatsapp_recipient || "");
    } catch {
      // Use defaults
    }
  };

  const loadLocalSettings = async () => {
    if (!window.electron) return;
    try {
      const settings = (await window.electron.settings.get()) as Record<string, unknown>;
      setWatchFolder((settings.watchFolder as string) || "");
      setAutoUploadEnabled((settings.autoUploadEnabled as boolean) || false);
      const running = await window.electron.watcher.status();
      setWatcherRunning(running);
    } catch {
      // Not in Electron
    }
  };

  const pickWatchFolder = async () => {
    if (!window.electron) return;
    const folder = await window.electron.dialogs.openFolder();
    if (folder) {
      setWatchFolder(folder);
      await window.electron.settings.set({ watchFolder: folder });
    }
  };

  const toggleAutoUpload = async () => {
    if (!window.electron) return;
    const newVal = !autoUploadEnabled;
    setAutoUploadEnabled(newVal);
    await window.electron.settings.set({ autoUploadEnabled: newVal });

    if (newVal && watchFolder) {
      await startWatcher();
    } else {
      await window.electron.watcher.stop();
      setWatcherRunning(false);
    }
  };

  const startWatcher = async () => {
    if (!window.electron || !watchFolder) return;
    const currentSettings = (await window.electron.settings.get()) as Record<string, unknown>;
    const token = localStorage.getItem("access_token") || "";
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";

    await window.electron.watcher.start({
      watchFolder,
      s3: {
        bucket: (currentSettings.s3Bucket as string) || "amzn-callsummery",
        region: (currentSettings.s3Region as string) || "eu-north-1",
        accessKeyId: (currentSettings.awsAccessKeyId as string) || "",
        secretAccessKey: (currentSettings.awsSecretAccessKey as string) || "",
      },
      webhook: {
        apiUrl,
        token,
      },
    });
    setWatcherRunning(true);
  };

  const saveSettings = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await apiClient.put("/settings/", {
        summary_language: language,
        notify_on_complete: notifyOnComplete,
        notification_method: notificationMethod,
        email_recipient: emailRecipient || null,
        whatsapp_recipient: whatsappRecipient || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // Error handled by client
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Settings</h1>

      {saved && (
        <div className="bg-green-50 text-green-600 p-3 rounded-lg text-sm">
          Settings saved!
        </div>
      )}

      {/* Auto-Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">Auto-Upload</h2>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Watch Folder
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={watchFolder}
              placeholder="Select a folder to monitor..."
              className="flex-1 p-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50"
            />
            <button
              onClick={pickWatchFolder}
              className="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-lg text-sm hover:bg-slate-200 transition-colors"
            >
              Browse
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            New audio files in this folder will be automatically uploaded and processed.
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm font-medium text-slate-700">Auto-upload enabled</span>
            {watcherRunning && (
              <span className="ml-2 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                Watching
              </span>
            )}
          </div>
          <button
            onClick={toggleAutoUpload}
            className={`relative w-11 h-6 rounded-full transition-colors ${
              autoUploadEnabled ? "bg-blue-600" : "bg-slate-300"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                autoUploadEnabled ? "translate-x-5" : ""
              }`}
            />
          </button>
        </div>

        {autoUploadEnabled && !watchFolder && (
          <p className="text-xs text-amber-600">Please select a watch folder to start monitoring.</p>
        )}
      </div>

      {/* Server Settings */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5">
        <h2 className="text-lg font-semibold text-slate-800">Preferences</h2>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Summary Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="p-2.5 border border-slate-200 rounded-lg text-sm w-full"
          >
            <option value="auto">Auto-detect</option>
            <option value="he">Hebrew</option>
            <option value="en">English</option>
          </select>
        </div>

        {/* Notifications */}
        <div>
          <div className="flex items-center gap-3 mb-3">
            <input
              type="checkbox"
              id="notify"
              checked={notifyOnComplete}
              onChange={(e) => setNotifyOnComplete(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="notify" className="text-sm font-medium text-slate-700">
              Notify when summary is ready
            </label>
          </div>

          {notifyOnComplete && (
            <div className="space-y-3 pl-6">
              <select
                value={notificationMethod}
                onChange={(e) => setNotificationMethod(e.target.value)}
                className="p-2.5 border border-slate-200 rounded-lg text-sm w-full"
              >
                <option value="email">Email only</option>
                <option value="whatsapp">WhatsApp only</option>
                <option value="both">Email + WhatsApp</option>
              </select>

              {(notificationMethod === "email" || notificationMethod === "both") && (
                <input
                  type="email"
                  placeholder="Email address"
                  value={emailRecipient}
                  onChange={(e) => setEmailRecipient(e.target.value)}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-sm"
                />
              )}

              {(notificationMethod === "whatsapp" || notificationMethod === "both") && (
                <input
                  type="text"
                  placeholder="WhatsApp number (e.g. +972501234567)"
                  value={whatsappRecipient}
                  onChange={(e) => setWhatsappRecipient(e.target.value)}
                  className="w-full p-2.5 border border-slate-200 rounded-lg text-sm"
                />
              )}
            </div>
          )}
        </div>

        <button
          onClick={saveSettings}
          disabled={saving}
          className="w-full bg-blue-600 text-white p-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
