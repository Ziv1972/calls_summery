/** To-do store - daily action items from call summaries and chat. */

import { create } from "zustand";
import apiClient from "../api/client";
import type { ActionLink, StructuredAction } from "../types/api";

export interface TodoItem {
  id: string;
  type: string;
  description: string;
  details: Record<string, unknown>;
  confidence: number;
  deep_link: string | null;
  source: "call" | "chat";
  callId?: string;
  completed: boolean;
}

interface TodoState {
  items: TodoItem[];
  loading: boolean;
  loadTodaysTodos: () => Promise<void>;
  addFromChat: (action: ActionLink) => void;
  toggleCompleted: (id: string) => void;
}

export const useTodoStore = create<TodoState>((set, get) => ({
  items: [],
  loading: false,

  loadTodaysTodos: async () => {
    set({ loading: true });

    try {
      const today = new Date().toISOString().split("T")[0];
      const { data: callsData } = await apiClient.get("/calls/", {
        params: { date_from: today, status: "completed", page_size: 50 },
      });

      const todos: TodoItem[] = [];

      // Fetch summaries concurrently
      const summaryResults = await Promise.allSettled(
        callsData.items.map((call: { id: string }) =>
          apiClient.get(`/summaries/call/${call.id}`).then((res) => ({
            callId: call.id,
            summary: res.data.data?.summary,
          }))
        )
      );

      for (const result of summaryResults) {
        if (result.status !== "fulfilled") continue;
        const { callId, summary } = result.value;
        if (!summary?.structured_actions) continue;

        for (const action of summary.structured_actions as StructuredAction[]) {
          todos.push({
            id: `${callId}-${action.type}-${action.description.slice(0, 20)}`,
            type: action.type,
            description: action.description,
            details: action.details,
            confidence: action.confidence,
            deep_link: null,
            source: "call",
            callId,
            completed: false,
          });
        }
      }

      // Merge with existing chat-sourced items
      const existing = get().items.filter((i) => i.source === "chat");
      set({ items: [...todos, ...existing], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addFromChat: (action: ActionLink) => {
    const item: TodoItem = {
      id: `chat-${Date.now()}`,
      type: action.type,
      description: action.description,
      details: action.details,
      confidence: action.confidence,
      deep_link: action.deep_link,
      source: "chat",
      completed: false,
    };
    set((state) => ({ items: [...state.items, item] }));
  },

  toggleCompleted: (id: string) => {
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, completed: !item.completed } : item
      ),
    }));
  },
}));
