/** Contacts list - search, tap to view calls with this person. */

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
import type { ApiResponse, Contact } from "@/src/types/api";

export default function ContactsListScreen() {
  const router = useRouter();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");

  const fetchContacts = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (query.trim()) params.q = query.trim();

      const { data } = await apiClient.get<ApiResponse<Contact[]>>(
        "/contacts/",
        { params },
      );
      if (data.data) setContacts(data.data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [query]);

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchContacts();
  }, [fetchContacts]);

  const renderItem = ({ item }: { item: Contact }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => router.push(`/(tabs)/contacts/${item.id}` as never)}
    >
      <View style={styles.avatar}>
        <FontAwesome name="user" size={20} color="#6B7280" />
      </View>
      <View style={styles.info}>
        <Text style={styles.name}>{item.name || item.phone_number}</Text>
        {item.company && <Text style={styles.meta}>{item.company}</Text>}
        <Text style={styles.phone}>{item.phone_number}</Text>
      </View>
      <FontAwesome name="chevron-right" size={14} color="#D1D5DB" />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.searchBar}
        placeholder="Search contacts..."
        value={query}
        onChangeText={setQuery}
        returnKeyType="search"
      />

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          data={contacts}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <View style={styles.empty}>
              <FontAwesome name="address-book-o" size={40} color="#D1D5DB" />
              <Text style={styles.emptyText}>No contacts yet</Text>
              <Text style={styles.emptySubtext}>
                Contacts are created automatically from call participants
              </Text>
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
  list: { padding: 16 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFF",
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    gap: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  info: { flex: 1 },
  name: { fontSize: 15, fontWeight: "600", color: "#111827" },
  meta: { fontSize: 13, color: "#6B7280", marginTop: 1 },
  phone: { fontSize: 13, color: "#9CA3AF", marginTop: 1 },
  empty: { alignItems: "center", paddingTop: 60, gap: 8 },
  emptyText: { fontSize: 16, color: "#9CA3AF" },
  emptySubtext: { fontSize: 13, color: "#D1D5DB", textAlign: "center", paddingHorizontal: 40 },
});
