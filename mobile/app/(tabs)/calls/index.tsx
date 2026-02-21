/** Calls list - paginated, searchable, filterable by status/sentiment. */

import { FontAwesome } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import type { ApiResponse, Call, PaginatedResponse } from "@/src/types/api";
import {
  formatDate,
  formatDuration,
  formatSentiment,
  formatStatus,
} from "@/src/utils/formatters";

const FILTERS = ["all", "completed", "transcribing", "summarizing", "failed"] as const;

export default function CallsListScreen() {
  const router = useRouter();
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const fetchCalls = useCallback(
    async (p: number, refresh: boolean) => {
      try {
        const params: Record<string, unknown> = { page: p, page_size: 20 };
        if (query.trim()) params.q = query.trim();
        if (statusFilter !== "all") params.status = statusFilter;

        const { data } = await apiClient.get<
          ApiResponse<PaginatedResponse<Call>>
        >("/calls/", { params });

        if (data.data) {
          const items = data.data.items;
          setCalls((prev) => (refresh ? items : [...prev, ...items]));
          setHasMore(p < data.data.total_pages);
        }
      } catch {
        // handle silently
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [query, statusFilter],
  );

  useEffect(() => {
    setLoading(true);
    setPage(1);
    fetchCalls(1, true);
  }, [fetchCalls]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setPage(1);
    fetchCalls(1, true);
  }, [fetchCalls]);

  const loadMore = useCallback(() => {
    if (!hasMore || loading) return;
    const next = page + 1;
    setPage(next);
    fetchCalls(next, false);
  }, [hasMore, loading, page, fetchCalls]);

  const renderItem = ({ item }: { item: Call }) => {
    const status = formatStatus(item.status);
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/(tabs)/calls/${item.id}` as never)}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.filename} numberOfLines={1}>
            {item.original_filename}
          </Text>
          <View style={[styles.badge, { backgroundColor: status.bg }]}>
            <Text style={[styles.badgeText, { color: status.text }]}>
              {status.label}
            </Text>
          </View>
        </View>
        <View style={styles.cardMeta}>
          <Text style={styles.metaText}>{formatDate(item.created_at)}</Text>
          {item.duration_seconds != null && (
            <Text style={styles.metaText}>
              {formatDuration(item.duration_seconds)}
            </Text>
          )}
          {item.caller_phone && (
            <Text style={styles.metaText}>{item.caller_phone}</Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.searchBar}
        placeholder="Search calls..."
        value={query}
        onChangeText={setQuery}
        returnKeyType="search"
      />

      <View style={styles.filters}>
        {FILTERS.map((f) => (
          <TouchableOpacity
            key={f}
            style={[
              styles.filterChip,
              statusFilter === f && styles.filterChipActive,
            ]}
            onPress={() => setStatusFilter(f)}
          >
            <Text
              style={[
                styles.filterText,
                statusFilter === f && styles.filterTextActive,
              ]}
            >
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && calls.length === 0 ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          data={calls}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <View style={styles.empty}>
              <FontAwesome name="search" size={32} color="#D1D5DB" />
              <Text style={styles.emptyText}>No calls found</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  searchBar: {
    marginHorizontal: 16,
    marginTop: 12,
    height: 44,
    backgroundColor: "#FFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
  },
  filters: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: "#E5E7EB",
  },
  filterChipActive: {
    backgroundColor: "#3B82F6",
  },
  filterText: {
    fontSize: 13,
    color: "#374151",
    fontWeight: "500",
  },
  filterTextActive: {
    color: "#FFF",
  },
  list: { paddingHorizontal: 16, paddingBottom: 20 },
  card: {
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
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  filename: {
    flex: 1,
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    marginRight: 8,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
  },
  cardMeta: {
    flexDirection: "row",
    gap: 12,
    marginTop: 6,
  },
  metaText: {
    fontSize: 13,
    color: "#6B7280",
  },
  empty: {
    alignItems: "center",
    paddingTop: 60,
    gap: 12,
  },
  emptyText: {
    fontSize: 15,
    color: "#9CA3AF",
  },
});
