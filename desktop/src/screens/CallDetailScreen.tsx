/** Call detail screen - summary, actions, transcript. */

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { ActionCard } from "../components/Actions/ActionCard";
import { formatDate, formatSentiment, formatStatus } from "../utils/formatters";
import type { CallDetail } from "../types/api";

export function CallDetailScreen() {
  const { callId } = useParams<{ callId: string }>();
  const [detail, setDetail] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTranscript, setShowTranscript] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (callId) loadDetail();
  }, [callId]);

  const loadDetail = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get(`/summaries/call/${callId}`);
      setDetail(data.data);
    } catch {
      setDetail(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-6 text-slate-400">Loading...</div>;
  if (!detail) return <div className="p-6 text-slate-400">Call not found</div>;

  const { call, summary, transcription } = detail;
  const st = formatStatus(call.status);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-5">
      {/* Back button */}
      <button
        onClick={() => navigate("/calls")}
        className="text-sm text-slate-500 hover:text-slate-800"
      >
        &larr; Back to Calls
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-5">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-800">{call.original_filename}</h1>
          <span className={`text-xs px-2.5 py-1 rounded-full ${st.color}`}>{st.label}</span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          {formatDate(call.created_at)}
          {call.caller_phone && ` \u00b7 ${call.caller_phone}`}
          {call.language_detected && ` \u00b7 ${call.language_detected.toUpperCase()}`}
        </p>
      </div>

      {/* Summary */}
      {summary && (
        <>
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="text-lg font-semibold mb-3">Summary</h2>
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
              {summary.summary_text}
            </p>

            {summary.topics && summary.topics.length > 0 && (
              <div className="flex gap-2 mt-4">
                {summary.topics.map((t) => (
                  <span key={t} className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
                    {t}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-4 mt-4 pt-4 border-t text-xs text-slate-500">
              <span>Sentiment: <strong className={formatSentiment(summary.sentiment).color}>{formatSentiment(summary.sentiment).label}</strong></span>
              <span>Model: {summary.model}</span>
              <span>Tokens: {summary.tokens_used}</span>
            </div>
          </div>

          {/* Key points */}
          {summary.key_points && summary.key_points.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="text-lg font-semibold mb-3">Key Points</h2>
              <ul className="space-y-2">
                {summary.key_points.map((p, i) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-700">
                    <span className="text-blue-500 mt-0.5">&#x2022;</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Structured actions */}
          {summary.structured_actions && summary.structured_actions.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="text-lg font-semibold mb-3">Suggested Actions</h2>
              <div className="space-y-2">
                {summary.structured_actions.map((action, i) => (
                  <ActionCard key={i} action={action} />
                ))}
              </div>
            </div>
          )}

          {/* Participants */}
          {summary.participants_details && summary.participants_details.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="text-lg font-semibold mb-3">Participants</h2>
              <div className="space-y-2">
                {summary.participants_details.map((p, i) => (
                  <div key={i} className="text-sm">
                    <strong>{p.name || p.speaker_label}</strong>
                    {p.role && <span className="text-slate-500"> ({p.role})</span>}
                    {p.phone && <span className="text-slate-400 ml-2">{p.phone}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Transcription */}
      {transcription && (
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            className="text-lg font-semibold w-full text-left flex justify-between items-center"
          >
            Transcription
            <span className="text-sm text-slate-400">{showTranscript ? "Hide" : "Show"}</span>
          </button>
          {showTranscript && (
            <div className="mt-4 space-y-2">
              {transcription.speakers ? (
                transcription.speakers.map((seg, i) => (
                  <div key={i} className="text-sm">
                    <strong className="text-blue-600">{seg.speaker}:</strong>{" "}
                    <span className="text-slate-700">{seg.text}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {transcription.text}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
