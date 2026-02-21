/** Contact detail - info, call history, "catch up" AI briefing. */

import { FontAwesome } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import type { ApiResponse, Call, Contact } from "@/src/types/api";
import { formatDate, formatDuration, formatStatus } from "@/src/utils/formatters";

export default function ContactDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [contact, setContact] = useState<Contact | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [catchUpText, setCatchUpText] = useState<string | null>(null);
  const [catchUpLoading, setCatchUpLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [contactRes, callsRes] = await Promise.all([
        apiClient.get<ApiResponse<Contact>>(`/contacts/${id}`),
        apiClient.get<ApiResponse<Call[]>>(`/contacts/${id}/calls`),
      ]);
      if (contactRes.data.data) setContact(contactRes.data.data);
      if (callsRes.data.data) setCalls(callsRes.data.data);
    } catch {
      Alert.alert("Error", "Failed to load contact");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCatchUp = async () => {
    if (catchUpLoading) return;
    setCatchUpLoading(true);
    try {
      const { data } = await apiClient.post<
        ApiResponse<{ response: string }>
      >("/chat/", {
        message: `Give me a brief catch-up summary to prepare for my next call with ${contact?.name || "this contact"}. Summarize the key topics, open items, and anything I should remember from our recent calls.`,
        contact_id: id,
      });
      setCatchUpText(data.data?.response || "No briefing available");
    } catch {
      Alert.alert("Error", "Failed to generate catch-up briefing");
    } finally {
      setCatchUpLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (!contact) return null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Contact info */}
      <View style={styles.infoCard}>
        <View style={styles.avatar}>
          <FontAwesome name="user" size={28} color="#6B7280" />
        </View>
        <Text style={styles.name}>{contact.name || contact.phone_number}</Text>
        <Text style={styles.phone}>{contact.phone_number}</Text>
        {contact.company && (
          <Text style={styles.meta}>{contact.company}</Text>
        )}
        {contact.email && <Text style={styles.meta}>{contact.email}</Text>}
        {contact.notes && (
          <Text style={styles.notes}>{contact.notes}</Text>
        )}
      </View>

      {/* Catch Up AI */}
      <TouchableOpacity
        style={styles.catchUpButton}
        onPress={handleCatchUp}
        disabled={catchUpLoading}
      >
        {catchUpLoading ? (
          <ActivityIndicator size="small" color="#3B82F6" />
        ) : (
          <FontAwesome name="magic" size={16} color="#3B82F6" />
        )}
        <Text style={styles.catchUpText}>Catch Up Before Next Call</Text>
      </TouchableOpacity>

      {catchUpText && (
        <View style={styles.catchUpCard}>
          <Text style={styles.catchUpTitle}>AI Briefing</Text>
          <Text style={styles.catchUpContent}>{catchUpText}</Text>
        </View>
      )}

      {/* Call history */}
      <Text style={styles.sectionTitle}>
        Call History ({calls.length})
      </Text>
      {calls.map((call) => {
        const status = formatStatus(call.status);
        return (
          <TouchableOpacity
            key={call.id}
            style={styles.callCard}
            onPress={() => router.push(`/(tabs)/calls/${call.id}` as never)}
          >
            <View style={styles.callRow}>
              <View style={styles.callInfo}>
                <Text style={styles.callName} numberOfLines={1}>
                  {call.original_filename}
                </Text>
                <Text style={styles.callMeta}>
                  {formatDate(call.created_at)}
                  {call.duration_seconds
                    ? ` \u00B7 ${formatDuration(call.duration_seconds)}`
                    : ""}
                </Text>
              </View>
              <View style={[styles.badge, { backgroundColor: status.bg }]}>
                <Text style={[styles.badgeText, { color: status.text }]}>
                  {status.label}
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        );
      })}

      {calls.length === 0 && (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No calls with this contact yet</Text>
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
  infoCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 20,
    alignItems: "center",
    marginBottom: 12,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  name: { fontSize: 20, fontWeight: "700", color: "#111827" },
  phone: { fontSize: 15, color: "#3B82F6", marginTop: 4 },
  meta: { fontSize: 14, color: "#6B7280", marginTop: 2 },
  notes: {
    fontSize: 13,
    color: "#9CA3AF",
    marginTop: 8,
    textAlign: "center",
    fontStyle: "italic",
  },
  catchUpButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#EFF6FF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  catchUpText: { fontSize: 15, color: "#3B82F6", fontWeight: "600" },
  catchUpCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
  },
  catchUpTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 8,
  },
  catchUpContent: { fontSize: 14, color: "#374151", lineHeight: 22 },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 10,
  },
  callCard: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  callRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  callInfo: { flex: 1, marginRight: 12 },
  callName: { fontSize: 14, fontWeight: "600", color: "#111827" },
  callMeta: { fontSize: 13, color: "#6B7280", marginTop: 2 },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  badgeText: { fontSize: 11, fontWeight: "600" },
  empty: { alignItems: "center", paddingTop: 20 },
  emptyText: { fontSize: 14, color: "#9CA3AF" },
});
