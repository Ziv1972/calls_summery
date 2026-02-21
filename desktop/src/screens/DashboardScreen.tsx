/** Dashboard - today's overview with briefing, to-dos, and quick stats. */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { useTodoStore } from "../store/todoStore";
import { ActionCard } from "../components/Actions/ActionCard";
import { formatDate, formatStatus } from "../utils/formatters";
import type { Call } from "../types/api";

export function DashboardScreen() {
  const [recentCalls, setRecentCalls] = useState<Call[]>([]);
  const [totalCalls, setTotalCalls] = useState(0);
  const { items: todos, loading: todosLoading, loadTodaysTodos, toggleCompleted } = useTodoStore();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboard();
    loadTodaysTodos();
  }, []);

  const loadDashboard = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const { data } = await apiClient.get("/calls/", {
        params: { date_from: today, page_size: 5 },
      });
      setRecentCalls(data.items);
      setTotalCalls(data.total);
    } catch {
      // Handle error silently on dashboard
    }
  };

  const pendingTodos = todos.filter((t) => !t.completed);
  const completedTodos = todos.filter((t) => t.completed);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">
        Today&apos;s Overview
      </h1>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Calls Today" value={totalCalls} color="blue" />
        <StatCard label="Pending Actions" value={pendingTodos.length} color="orange" />
        <StatCard label="Completed" value={completedTodos.length} color="green" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* To-do list */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            Action Items
          </h2>
          {todosLoading ? (
            <p className="text-sm text-slate-400">Loading...</p>
          ) : pendingTodos.length === 0 ? (
            <p className="text-sm text-slate-400">
              No pending actions. Use the AI Chat to create tasks!
            </p>
          ) : (
            <div className="space-y-2">
              {pendingTodos.map((todo) => (
                <div key={todo.id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={todo.completed}
                    onChange={() => toggleCompleted(todo.id)}
                    className="rounded"
                  />
                  <ActionCard
                    action={{
                      type: todo.type as "task",
                      description: todo.description,
                      details: todo.details,
                      confidence: todo.confidence,
                    }}
                    compact
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent calls */}
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">
            Recent Calls
          </h2>
          {recentCalls.length === 0 ? (
            <p className="text-sm text-slate-400">No calls today</p>
          ) : (
            <div className="space-y-3">
              {recentCalls.map((call) => {
                const status = formatStatus(call.status);
                return (
                  <div
                    key={call.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-slate-50 cursor-pointer"
                    onClick={() => navigate(`/calls/${call.id}`)}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {call.original_filename}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(call.created_at)}
                        {call.caller_phone && ` - ${call.caller_phone}`}
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${status.color}`}>
                      {status.label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: "text-blue-600 bg-blue-50 border-blue-100",
    orange: "text-orange-600 bg-orange-50 border-orange-100",
    green: "text-green-600 bg-green-50 border-green-100",
  };
  return (
    <div className={`rounded-xl border p-5 text-center ${colors[color] || colors.blue}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm opacity-75 mt-1">{label}</div>
    </div>
  );
}
