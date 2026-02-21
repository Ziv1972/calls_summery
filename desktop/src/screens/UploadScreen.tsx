/** Upload screen - manual file upload with language selection. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";

export function UploadScreen() {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("auto");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("language", language);

      const { data } = await apiClient.post("/calls/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });

      const callId = data.data?.id;
      setSuccess("Upload successful! Processing started.");
      setFile(null);

      // Navigate to call detail after short delay
      if (callId) {
        setTimeout(() => navigate(`/calls/${callId}`), 1500);
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Object && "response" in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Upload failed")
          : "Upload failed";
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">Upload Recording</h1>

      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-5">
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>
        )}
        {success && (
          <div className="bg-green-50 text-green-600 p-3 rounded-lg text-sm">{success}</div>
        )}

        {/* File picker */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Audio File
          </label>
          <input
            type="file"
            accept="audio/*,.mp3,.m4a,.wav,.ogg,.webm,.flac,.mp4"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {file && (
            <p className="text-xs text-slate-500 mt-1">
              {file.name} ({(file.size / (1024 * 1024)).toFixed(1)} MB)
            </p>
          )}
        </div>

        {/* Language selector */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Language
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

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full bg-blue-600 text-white p-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
        >
          {uploading ? "Uploading..." : "Upload & Process"}
        </button>
      </div>
    </div>
  );
}
