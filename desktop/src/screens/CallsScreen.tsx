/** Calls list with search, filters, and pagination. */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { formatDate, formatDuration, formatFileSize, formatStatus } from "../utils/formatters";
import type { Call } from "../types/api";

export function CallsScreen() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadCalls();
  }, [page, search, sentiment, status]);

  const loadCalls = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (search) params.q = search;
      if (sentiment) params.sentiment = sentiment;
      if (status) params.status = status;

      const { data } = await apiClient.get("/calls/", { params });
      setCalls(data.items);
      setTotal(data.total);
    } catch {
      // Error handled by API client
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Call History</h1>
        <span className="text-sm text-slate-500">{total} calls</span>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <input
          type="text"
          placeholder="Search calls..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 p-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <select
          value={sentiment}
          onChange={(e) => { setSentiment(e.target.value); setPage(1); }}
          className="p-2.5 border border-slate-200 rounded-lg text-sm"
        >
          <option value="">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
          <option value="mixed">Mixed</option>
        </select>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="p-2.5 border border-slate-200 rounded-lg text-sm"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="transcribing">Transcribing</option>
          <option value="summarizing">Summarizing</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Call list */}
      <div className="bg-white rounded-xl shadow-sm border divide-y">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading...</div>
        ) : calls.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No calls found</div>
        ) : (
          calls.map((call) => {
            const st = formatStatus(call.status);
            return (
              <div
                key={call.id}
                className="flex items-center gap-4 p-4 hover:bg-slate-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/calls/${call.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{call.original_filename}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatDate(call.created_at)}
                    {call.caller_phone && ` \u00b7 ${call.caller_phone}`}
                    {call.duration_seconds && ` \u00b7 ${formatDuration(call.duration_seconds)}`}
                    {` \u00b7 ${formatFileSize(call.file_size_bytes)}`}
                  </p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full shrink-0 ${st.color}`}>
                  {st.label}
                </span>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30"
          >
            Previous
          </button>
          <span className="px-3 py-1.5 text-sm text-slate-600">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
