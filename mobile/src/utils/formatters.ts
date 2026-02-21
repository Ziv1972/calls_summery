/** Formatting utilities for dates, durations, file sizes. */

import { format, formatDistanceToNow, isToday, isYesterday } from "date-fns";

export function formatDuration(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return "\u2014";
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

export type StatusStyle = {
  label: string;
  bg: string;
  text: string;
};

export function formatStatus(status: string): StatusStyle {
  const map: Record<string, StatusStyle> = {
    uploaded: { label: "Uploaded", bg: "#E5E7EB", text: "#374151" },
    transcribing: { label: "Transcribing", bg: "#DBEAFE", text: "#1E40AF" },
    transcribed: { label: "Transcribed", bg: "#BFDBFE", text: "#1E40AF" },
    summarizing: { label: "Summarizing", bg: "#EDE9FE", text: "#6D28D9" },
    completed: { label: "Completed", bg: "#D1FAE5", text: "#065F46" },
    failed: { label: "Failed", bg: "#FEE2E2", text: "#991B1B" },
  };
  return map[status] ?? { label: status, bg: "#F3F4F6", text: "#6B7280" };
}

export type SentimentStyle = {
  label: string;
  color: string;
};

export function formatSentiment(
  sentiment: string | null,
): SentimentStyle {
  if (!sentiment) return { label: "\u2014", color: "#9CA3AF" };
  const map: Record<string, SentimentStyle> = {
    positive: { label: "Positive", color: "#059669" },
    negative: { label: "Negative", color: "#DC2626" },
    neutral: { label: "Neutral", color: "#6B7280" },
    mixed: { label: "Mixed", color: "#D97706" },
  };
  return map[sentiment] ?? { label: sentiment, color: "#6B7280" };
}
