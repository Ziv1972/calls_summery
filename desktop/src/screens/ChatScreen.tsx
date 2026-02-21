/** AI Companion chat screen. */

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import { useTodoStore } from "../store/todoStore";
import { ActionCard } from "../components/Actions/ActionCard";
import type { ActionLink } from "../types/api";

export function ChatScreen() {
  const { messages, isProcessing, sendMessage } = useChatStore();
  const addFromChat = useTodoStore((s) => s.addFromChat);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isProcessing) return;
    setInput("");
    await sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAddTodo = (action: ActionLink) => {
    addFromChat(action);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 bg-white border-b">
        <h1 className="text-lg font-bold text-slate-800">AI Companion</h1>
        <p className="text-xs text-slate-500">
          Tell me about your calls and I&apos;ll create actions for you
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xl rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border shadow-sm"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {msg.actions && msg.actions.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.actions.map((action, j) => (
                    <div key={j} className="flex items-center gap-2">
                      <div className="flex-1">
                        <ActionCard
                          action={{
                            type: action.type,
                            description: action.description,
                            details: action.details,
                            confidence: action.confidence,
                          }}
                          compact
                        />
                      </div>
                      <button
                        onClick={() => handleAddTodo(action)}
                        className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                        title="Add to today's to-do"
                      >
                        + Todo
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-white border shadow-sm rounded-2xl px-4 py-3">
              <p className="text-sm text-slate-400">Thinking...</p>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tell me about a call, or ask me to create an action..."
            rows={2}
            className="flex-1 p-3 border border-slate-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className="px-5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
