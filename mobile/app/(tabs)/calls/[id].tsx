/** Call detail - summary, key points, actions, AI chat, transcription. */

import { FontAwesome } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import type {
  ActionLink,
  ApiResponse,
  CallDetail,
  ChatMessage,
  StructuredAction,
} from "@/src/types/api";
import { generateDeepLink } from "@/src/utils/deepLinks";
import {
  formatDate,
  formatDuration,
  formatSentiment,
  formatStatus,
} from "@/src/utils/formatters";

const ACTION_ICONS: Record<string, React.ComponentProps<typeof FontAwesome>["name"]> = {
  calendar_event: "calendar",
  send_email: "envelope",
  send_whatsapp: "whatsapp",
  reminder: "bell",
  task: "check-square-o",
};

const ACTION_COLORS: Record<string, string> = {
  calendar_event: "#3B82F6",
  send_email: "#F97316",
  send_whatsapp: "#22C55E",
  reminder: "#8B5CF6",
  task: "#64748B",
};

export default function CallDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [detail, setDetail] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTranscript, setShowTranscript] = useState(false);

  // AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);

  const fetchDetail = useCallback(async () => {
    try {
      const [callRes, summaryRes] = await Promise.all([
        apiClient.get<ApiResponse<CallDetail["call"]>>(`/calls/${id}`),
        apiClient
          .get<ApiResponse<CallDetail["summary"]>>(`/summaries/call/${id}`)
          .catch(() => ({ data: { data: null } })),
      ]);

      setDetail({
        call: callRes.data.data!,
        summary: (summaryRes.data as ApiResponse<CallDetail["summary"]>).data,
        transcription: null,
      });
    } catch {
      Alert.alert("Error", "Failed to load call details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // Poll for in-progress calls
  useEffect(() => {
    if (!detail?.call) return;
    const inProgress =
      detail.call.status === "transcribing" ||
      detail.call.status === "summarizing" ||
      detail.call.status === "uploaded";
    if (!inProgress) return;

    const interval = setInterval(fetchDetail, 10_000);
    return () => clearInterval(interval);
  }, [detail?.call?.status, fetchDetail]);

  const handleOpenAction = async (action: StructuredAction) => {
    const url = generateDeepLink(action);
    if (!url) return;
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    } else {
      Alert.alert("Cannot Open", "No app available to handle this action");
    }
  };

  const sendChatMessage = async () => {
    const text = chatInput.trim();
    if (!text || chatLoading) return;

    const userMsg: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const { data } = await apiClient.post<
        ApiResponse<{ response: string; actions?: ActionLink[] }>
      >("/chat/", {
        message: text,
        call_id: id,
      });

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.data?.response || "No response",
        actions: data.data?.actions,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!detail) return null;

  const { call, summary } = detail;
  const status = formatStatus(call.status);
  const sentiment = summary ? formatSentiment(summary.sentiment) : null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.headerCard}>
        <Text style={styles.headerTitle} numberOfLines={2}>
          {call.original_filename}
        </Text>
        <View style={styles.headerMeta}>
          <View style={[styles.badge, { backgroundColor: status.bg }]}>
            <Text style={[styles.badgeText, { color: status.text }]}>
              {status.label}
            </Text>
          </View>
          {sentiment && (
            <Text style={[styles.sentimentText, { color: sentiment.color }]}>
              {sentiment.label}
            </Text>
          )}
        </View>
        <Text style={styles.metaText}>
          {formatDate(call.created_at)}
          {call.duration_seconds ? ` \u00B7 ${formatDuration(call.duration_seconds)}` : ""}
        </Text>
      </View>

      {/* Summary */}
      {summary && (
        <>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Summary</Text>
            <Text style={styles.summaryText}>{summary.summary_text}</Text>
          </View>

          {/* Topics */}
          {summary.topics && summary.topics.length > 0 && (
            <View style={styles.tagsRow}>
              {summary.topics.map((topic, i) => (
                <View key={i} style={styles.tag}>
                  <Text style={styles.tagText}>{topic}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Key Points */}
          {summary.key_points && summary.key_points.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Key Points</Text>
              {summary.key_points.map((point, i) => (
                <View key={i} style={styles.bulletRow}>
                  <Text style={styles.bullet}>{"\u2022"}</Text>
                  <Text style={styles.bulletText}>{point}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Structured Actions */}
          {summary.structured_actions &&
            summary.structured_actions.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Actions</Text>
                {summary.structured_actions.map((action, i) => {
                  const icon = ACTION_ICONS[action.type] || "bolt";
                  const color = ACTION_COLORS[action.type] || "#6B7280";
                  const link = generateDeepLink(action);
                  return (
                    <TouchableOpacity
                      key={i}
                      style={styles.actionCard}
                      onPress={() => handleOpenAction(action)}
                      disabled={!link}
                    >
                      <View
                        style={[styles.actionIcon, { backgroundColor: color + "20" }]}
                      >
                        <FontAwesome name={icon} size={18} color={color} />
                      </View>
                      <View style={styles.actionInfo}>
                        <Text style={styles.actionDesc}>{action.description}</Text>
                        <Text style={styles.actionConf}>
                          {Math.round(action.confidence * 100)}% confidence
                        </Text>
                      </View>
                      {link && (
                        <FontAwesome name="external-link" size={14} color="#9CA3AF" />
                      )}
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

          {/* Participants */}
          {summary.participants_details &&
            summary.participants_details.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Participants</Text>
                {summary.participants_details.map((p, i) => (
                  <View key={i} style={styles.participantRow}>
                    <FontAwesome name="user" size={14} color="#6B7280" />
                    <Text style={styles.participantText}>
                      {p.name || p.speaker_label}
                      {p.role ? ` (${p.role})` : ""}
                      {p.phone ? ` \u00B7 ${p.phone}` : ""}
                    </Text>
                  </View>
                ))}
              </View>
            )}
        </>
      )}

      {/* In-progress indicator */}
      {(call.status === "transcribing" || call.status === "summarizing") && (
        <View style={styles.progressCard}>
          <ActivityIndicator size="small" color="#3B82F6" />
          <Text style={styles.progressText}>
            {call.status === "transcribing"
              ? "Transcribing audio..."
              : "Generating summary..."}
          </Text>
        </View>
      )}

      {/* AI Chat Toggle */}
      {summary && (
        <TouchableOpacity
          style={styles.chatToggle}
          onPress={() => setShowChat(!showChat)}
        >
          <FontAwesome name="comment" size={16} color="#3B82F6" />
          <Text style={styles.chatToggleText}>
            {showChat ? "Hide AI Chat" : "Ask AI About This Call"}
          </Text>
        </TouchableOpacity>
      )}

      {/* Chat Section */}
      {showChat && (
        <View style={styles.chatSection}>
          {chatMessages.map((msg, i) => (
            <View
              key={i}
              style={[
                styles.chatBubble,
                msg.role === "user" ? styles.userBubble : styles.assistantBubble,
              ]}
            >
              <Text
                style={
                  msg.role === "user"
                    ? styles.userBubbleText
                    : styles.assistantBubbleText
                }
              >
                {msg.content}
              </Text>
            </View>
          ))}
          {chatLoading && (
            <ActivityIndicator
              size="small"
              color="#3B82F6"
              style={{ marginVertical: 8 }}
            />
          )}
          <View style={styles.chatInputRow}>
            <TextInput
              style={styles.chatInput}
              placeholder="Ask about this call..."
              value={chatInput}
              onChangeText={setChatInput}
              onSubmitEditing={sendChatMessage}
              returnKeyType="send"
            />
            <TouchableOpacity
              style={styles.chatSendButton}
              onPress={sendChatMessage}
              disabled={chatLoading || !chatInput.trim()}
            >
              <FontAwesome
                name="send"
                size={16}
                color={chatInput.trim() ? "#3B82F6" : "#D1D5DB"}
              />
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Transcription toggle */}
      {summary && (
        <TouchableOpacity
          style={styles.transcriptToggle}
          onPress={() => setShowTranscript(!showTranscript)}
        >
          <Text style={styles.transcriptToggleText}>
            {showTranscript ? "Hide Transcription" : "Show Transcription"}
          </Text>
          <FontAwesome
            name={showTranscript ? "chevron-up" : "chevron-down"}
            size={12}
            color="#6B7280"
          />
        </TouchableOpacity>
      )}

      {showTranscript && detail.transcription && (
        <View style={styles.section}>
          <Text style={styles.transcriptText}>{detail.transcription.text}</Text>
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  content: { padding: 16 },
  headerCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  headerTitle: { fontSize: 18, fontWeight: "700", color: "#111827" },
  headerMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 8,
  },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { fontSize: 12, fontWeight: "600" },
  sentimentText: { fontSize: 13, fontWeight: "600" },
  metaText: { fontSize: 13, color: "#6B7280", marginTop: 6 },
  section: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 10,
  },
  summaryText: { fontSize: 15, color: "#374151", lineHeight: 22 },
  tagsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  tag: {
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: { fontSize: 12, color: "#1E40AF", fontWeight: "500" },
  bulletRow: { flexDirection: "row", marginBottom: 6, paddingRight: 8 },
  bullet: { fontSize: 15, color: "#3B82F6", marginRight: 8, lineHeight: 22 },
  bulletText: { flex: 1, fontSize: 14, color: "#374151", lineHeight: 22 },
  actionCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    backgroundColor: "#F9FAFB",
    borderRadius: 10,
    marginBottom: 8,
    gap: 12,
  },
  actionIcon: {
    width: 38,
    height: 38,
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
  },
  actionInfo: { flex: 1 },
  actionDesc: { fontSize: 14, color: "#111827", fontWeight: "500" },
  actionConf: { fontSize: 12, color: "#9CA3AF", marginTop: 2 },
  participantRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  participantText: { fontSize: 14, color: "#374151" },
  progressCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#EFF6FF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  progressText: { fontSize: 14, color: "#1E40AF", fontWeight: "500" },
  chatToggle: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#EFF6FF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  chatToggleText: { fontSize: 15, color: "#3B82F6", fontWeight: "600" },
  chatSection: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 12,
    marginBottom: 12,
  },
  chatBubble: { borderRadius: 12, padding: 12, marginBottom: 8, maxWidth: "85%" },
  userBubble: { backgroundColor: "#3B82F6", alignSelf: "flex-end" },
  assistantBubble: { backgroundColor: "#F3F4F6", alignSelf: "flex-start" },
  userBubbleText: { color: "#FFF", fontSize: 14 },
  assistantBubbleText: { color: "#111827", fontSize: 14, lineHeight: 20 },
  chatInputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
  },
  chatInput: {
    flex: 1,
    height: 42,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 20,
    paddingHorizontal: 14,
    fontSize: 14,
  },
  chatSendButton: { padding: 10 },
  transcriptToggle: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 12,
    marginBottom: 12,
  },
  transcriptToggleText: { fontSize: 14, color: "#6B7280", fontWeight: "500" },
  transcriptText: { fontSize: 14, color: "#374151", lineHeight: 22 },
});
