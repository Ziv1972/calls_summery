/** Chat store - AI companion conversation via IPC (Electron) or backend API (browser). */

import { create } from "zustand";
import apiClient from "../api/client";
import type { ActionLink } from "../types/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  actions?: ActionLink[];
  timestamp: string;
}

interface ChatState {
  messages: ChatMessage[];
  isProcessing: boolean;
  sendMessage: (text: string) => Promise<void>;
  clearChat: () => void;
}

const SYSTEM_PROMPT = `You are an AI assistant for the Calls Summary app. You help users manage follow-up actions from phone calls.

When the user tells you about a call or task, extract actionable items and return a JSON object:
{
  "response": "A friendly natural language response",
  "actions": [
    {
      "type": "calendar_event" | "send_email" | "send_whatsapp" | "reminder" | "task",
      "description": "Human-readable description",
      "details": { ... type-specific fields ... },
      "confidence": 0.0 to 1.0
    }
  ]
}

Type-specific details:
- calendar_event: { title, date (YYYY-MM-DD), time (HH:MM), duration_minutes }
- send_email: { to_email, subject, body_outline }
- send_whatsapp: { phone, message_outline }
- reminder: { date, time, note }
- task: { title, due_date, priority }

If no actions are needed, return an empty actions array.
Today's date is ${new Date().toISOString().split("T")[0]}.
Always respond in the same language the user writes in.`;

const RATE_LIMIT_MS = 2000;
let lastRequestTime = 0;

async function sendChatMessage(
  messages: Array<{ role: string; content: string }>,
  systemPrompt: string,
): Promise<string> {
  // Electron: use secure IPC (API key in main process)
  if (window.electron?.chat) {
    return window.electron.chat.send(messages, systemPrompt);
  }

  // Browser fallback: call backend chat endpoint
  const { data } = await apiClient.post("/chat/", {
    messages,
    system_prompt: systemPrompt,
  });
  return data.data?.response ?? data.data ?? "";
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    {
      role: "assistant",
      content:
        "Hi! Tell me about your calls and I'll help you take action - schedule meetings, send emails, create reminders.",
      timestamp: new Date().toISOString(),
    },
  ],
  isProcessing: false,

  sendMessage: async (text: string) => {
    // Rate limiting
    const now = Date.now();
    if (now - lastRequestTime < RATE_LIMIT_MS) {
      return;
    }
    lastRequestTime = now;

    const userMsg: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isProcessing: true,
    }));

    try {
      const history = get()
        .messages.filter((m) => m.role !== "assistant" || m.content !== get().messages[0].content)
        .map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
        }));

      const assistantText = await sendChatMessage(
        [...history, { role: "user", content: text }],
        SYSTEM_PROMPT,
      );

      let parsed: { response: string; actions: ActionLink[] };
      try {
        parsed = JSON.parse(assistantText);
        if (typeof parsed.response !== "string" || !Array.isArray(parsed.actions)) {
          parsed = { response: assistantText, actions: [] };
        }
      } catch {
        parsed = { response: assistantText, actions: [] };
      }

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: parsed.response,
        actions: parsed.actions,
        timestamp: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMsg],
        isProcessing: false,
      }));
    } catch (error) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, errorMsg],
        isProcessing: false,
      }));
    }
  },

  clearChat: () =>
    set({
      messages: [
        {
          role: "assistant",
          content:
            "Hi! Tell me about your calls and I'll help you take action - schedule meetings, send emails, create reminders.",
          timestamp: new Date().toISOString(),
        },
      ],
    }),
}));
