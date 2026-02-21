/** Deep link generation for structured actions. */

import type { StructuredAction } from "../types/api";

export function generateDeepLink(action: StructuredAction): string | null {
  switch (action.type) {
    case "calendar_event":
      return calendarLink(action.details);
    case "send_email":
      return emailLink(action.details);
    case "send_whatsapp":
      return whatsappLink(action.details);
    default:
      return null;
  }
}

function calendarLink(details: Record<string, unknown>): string | null {
  const date = details.date as string | undefined;
  const title = (details.title as string) || "Event";
  if (!date) return null;

  const dateClean = date.replace(/-/g, "");
  const time = details.time as string | undefined;
  const duration = (details.duration_minutes as number) || 60;

  let startStr: string;
  let endStr: string;

  if (time) {
    const [h, m] = time.split(":").map(Number);
    startStr = `${dateClean}T${String(h).padStart(2, "0")}${String(m).padStart(2, "0")}00`;
    const endMinutes = h * 60 + m + duration;
    const endH = Math.floor(endMinutes / 60) % 24;
    const endM = endMinutes % 60;
    endStr = `${dateClean}T${String(endH).padStart(2, "0")}${String(endM).padStart(2, "0")}00`;
  } else {
    startStr = `${dateClean}T090000`;
    endStr = `${dateClean}T100000`;
  }

  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${startStr}/${endStr}`;
}

function emailLink(details: Record<string, unknown>): string | null {
  const to = (details.to_email as string) || "";
  const subject = (details.subject as string) || "";
  const body = (details.body_outline as string) || "";
  return `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function whatsappLink(details: Record<string, unknown>): string | null {
  const phone = details.phone as string | undefined;
  if (!phone) return null;
  const clean = phone.replace(/[^\d]/g, "");
  const message = (details.message_outline as string) || "";
  return `https://wa.me/${clean}${message ? `?text=${encodeURIComponent(message)}` : ""}`;
}
