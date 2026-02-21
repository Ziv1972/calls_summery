/** Action card with icon, description, and deep link button. */

import type { StructuredAction } from "../../types/api";
import { generateDeepLink } from "../../utils/deepLinks";

const ACTION_ICONS: Record<string, string> = {
  calendar_event: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
  send_email: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  send_whatsapp: "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z",
  reminder: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  task: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
};

const ACTION_COLORS: Record<string, string> = {
  calendar_event: "bg-blue-50 border-blue-200 text-blue-700",
  send_email: "bg-orange-50 border-orange-200 text-orange-700",
  send_whatsapp: "bg-green-50 border-green-200 text-green-700",
  reminder: "bg-purple-50 border-purple-200 text-purple-700",
  task: "bg-slate-50 border-slate-200 text-slate-700",
};

interface ActionCardProps {
  action: StructuredAction;
  compact?: boolean;
}

export function ActionCard({ action, compact = false }: ActionCardProps) {
  const deepLink = generateDeepLink(action);
  const iconPath = ACTION_ICONS[action.type] || ACTION_ICONS.task;
  const colorClass = ACTION_COLORS[action.type] || ACTION_COLORS.task;

  const handleClick = () => {
    if (deepLink) {
      window.open(deepLink, "_blank");
    }
  };

  return (
    <div
      className={`flex items-center gap-3 border rounded-lg ${colorClass} ${compact ? "p-2" : "p-3"} ${deepLink ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
      onClick={handleClick}
    >
      <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPath} />
      </svg>

      <div className="flex-1 min-w-0">
        <p className={`${compact ? "text-xs" : "text-sm"} font-medium truncate`}>
          {action.description}
        </p>
        {!compact && (
          <p className="text-xs opacity-60 mt-0.5">
            {action.type.replace("_", " ")} &middot; {Math.round(action.confidence * 100)}%
          </p>
        )}
      </div>

      {deepLink && (
        <svg className="w-4 h-4 shrink-0 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      )}
    </div>
  );
}
