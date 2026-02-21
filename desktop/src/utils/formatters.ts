/** Formatting utilities for dates, durations, file sizes. */

import { format, formatDistanceToNow, isToday, isYesterday } from "date-fns";

export function formatDuration(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  if (isToday(date)) return `Today ${format(date, "HH:mm")}`;
  if (isYesterday(date)) return `Yesterday ${format(date, "HH:mm")}`;
  return format(date, "MMM d, yyyy HH:mm");
}

export function formatRelative(dateStr: string): string {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
}

export function formatStatus(status: string): { label: string; color: string } {
  const map: Record<string, { label: string; color: string }> = {
    uploaded: { label: "Uploaded", color: "bg-gray-200 text-gray-800" },
    transcribing: { label: "Transcribing", color: "bg-blue-100 text-blue-800" },
    transcribed: { label: "Transcribed", color: "bg-blue-200 text-blue-800" },
    summarizing: { label: "Summarizing", color: "bg-purple-100 text-purple-800" },
    completed: { label: "Completed", color: "bg-green-100 text-green-800" },
    failed: { label: "Failed", color: "bg-red-100 text-red-800" },
  };
  return map[status] ?? { label: status, color: "bg-gray-100 text-gray-600" };
}

export function formatSentiment(sentiment: string | null): { label: string; color: string } {
  if (!sentiment) return { label: "—", color: "text-gray-400" };
  const map: Record<string, { label: string; color: string }> = {
    positive: { label: "Positive", color: "text-green-600" },
    negative: { label: "Negative", color: "text-red-600" },
    neutral: { label: "Neutral", color: "text-gray-600" },
    mixed: { label: "Mixed", color: "text-yellow-600" },
  };
  return map[sentiment] ?? { label: sentiment, color: "text-gray-600" };
}
