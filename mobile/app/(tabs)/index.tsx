/** Dashboard - recent calls, stats, pending actions. */

import { FontAwesome } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import { useAuthStore } from "@/src/stores/authStore";
import type { ApiResponse, Call, PaginatedResponse } from "@/src/types/api";
import { formatDate, formatDuration, formatStatus } from "@/src/utils/formatters";

export default function DashboardScreen() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRecentCalls = useCallback(async () => {
    try {
      const { data } = await apiClient.get<ApiResponse<PaginatedResponse<Call>>>(
        "/calls/",
        { params: { page: 1, page_size: 10 } },
      );
      if (data.data) setCalls(data.data.items);
    } catch {
      // silently fail on dashboard
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRecentCalls();
  }, [fetchRecentCalls]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchRecentCalls();
  }, [fetchRecentCalls]);

  const completedCount = calls.filter((c) => c.status === "completed").length;
  const processingCount = calls.filter(
    (c) => c.status === "transcribing" || c.status === "summarizing",
  ).length;

  const renderCallItem = ({ item }: { item: Call }) => {
    const status = formatStatus(item.status);
    return (
      <TouchableOpacity
        style={styles.callCard}
        onPress={() => router.push(`/(tabs)/calls/${item.id}` as never)}
      >
        <View style={styles.callRow}>
          <View style={styles.callInfo}>
            <Text style={styles.callName} numberOfLines={1}>
              {item.original_filename}
            </Text>
            <Text style={styles.callMeta}>
              {formatDate(item.created_at)}
              {item.duration_seconds ? ` \u00B7 ${formatDuration(item.duration_seconds)}` : ""}
            </Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: status.bg }]}>
            <Text style={[styles.statusText, { color: status.text }]}>
              {status.label}
            </Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <FlatList
      data={calls}
      keyExtractor={(item) => item.id}
      renderItem={renderCallItem}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
      contentContainerStyle={styles.list}
      ListHeaderComponent={
        <View>
          <Text style={styles.greeting}>
            Hello, {user?.name || user?.email?.split("@")[0] || "there"}
          </Text>

          <View style={styles.statsRow}>
            <View style={styles.statCard}>
              <FontAwesome name="phone" size={20} color="#3B82F6" />
              <Text style={styles.statNumber}>{calls.length}</Text>
              <Text style={styles.statLabel}>Recent</Text>
            </View>
            <View style={styles.statCard}>
              <FontAwesome name="check-circle" size={20} color="#10B981" />
              <Text style={styles.statNumber}>{completedCount}</Text>
              <Text style={styles.statLabel}>Completed</Text>
            </View>
            <View style={styles.statCard}>
              <FontAwesome name="spinner" size={20} color="#F59E0B" />
              <Text style={styles.statNumber}>{processingCount}</Text>
              <Text style={styles.statLabel}>Processing</Text>
            </View>
          </View>

          <Text style={styles.sectionTitle}>Recent Calls</Text>
        </View>
      }
      ListEmptyComponent={
        <View style={styles.empty}>
          <FontAwesome name="phone" size={40} color="#D1D5DB" />
          <Text style={styles.emptyText}>No calls yet</Text>
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={() => router.push("/(tabs)/upload" as never)}
          >
            <Text style={styles.uploadButtonText}>Upload Your First Call</Text>
          </TouchableOpacity>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  list: { padding: 16 },
  greeting: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    gap: 6,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statNumber: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
  },
  statLabel: {
    fontSize: 12,
    color: "#6B7280",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  callCard: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  callRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  callInfo: { flex: 1, marginRight: 12 },
  callName: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },
  callMeta: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: "600",
  },
  empty: {
    alignItems: "center",
    paddingTop: 40,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
    color: "#9CA3AF",
  },
  uploadButton: {
    backgroundColor: "#3B82F6",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
    marginTop: 8,
  },
  uploadButtonText: {
    color: "#FFF",
    fontWeight: "600",
    fontSize: 15,
  },
});
