/** Settings screen - language, notifications, account info, logout. */

import { FontAwesome } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Platform,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import { useAuthStore } from "@/src/stores/authStore";
import type { ApiResponse, UserSettings } from "@/src/types/api";

const LANGUAGES = [
  { value: "auto", label: "Auto-detect" },
  { value: "he", label: "Hebrew" },
  { value: "en", label: "English" },
];

const NOTIFY_METHODS = [
  { value: "none", label: "None" },
  { value: "email", label: "Email" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "both", label: "Both" },
];

export default function SettingsScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const { data } = await apiClient.get<ApiResponse<UserSettings>>(
        "/settings/",
      );
      if (data.data) setSettings(data.data);
    } catch {
      // use defaults
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const saveSettings = async (update: Partial<UserSettings>) => {
    if (!settings) return;
    const updated = { ...settings, ...update };
    setSettings(updated);
    setSaving(true);
    try {
      await apiClient.put("/settings/", updated);
    } catch {
      Alert.alert("Error", "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert("Logout", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Logout",
        style: "destructive",
        onPress: () => {
          logout();
          router.replace("/(auth)/login" as never);
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Account */}
      <Text style={styles.sectionHeader}>Account</Text>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.label}>Email</Text>
          <Text style={styles.value}>{user?.email}</Text>
        </View>
        <View style={styles.row}>
          <Text style={styles.label}>Plan</Text>
          <Text style={styles.planBadge}>
            {user?.plan?.toUpperCase() || "FREE"}
          </Text>
        </View>
      </View>

      {/* Summary Language */}
      <Text style={styles.sectionHeader}>Summary Language</Text>
      <View style={styles.card}>
        <View style={styles.chipRow}>
          {LANGUAGES.map((lang) => (
            <TouchableOpacity
              key={lang.value}
              style={[
                styles.chip,
                settings?.summary_language === lang.value &&
                  styles.chipActive,
              ]}
              onPress={() => saveSettings({ summary_language: lang.value })}
            >
              <Text
                style={[
                  styles.chipText,
                  settings?.summary_language === lang.value &&
                    styles.chipTextActive,
                ]}
              >
                {lang.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Notifications */}
      <Text style={styles.sectionHeader}>Notifications</Text>
      <View style={styles.card}>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Notify on completion</Text>
          <Switch
            value={settings?.notify_on_complete ?? false}
            onValueChange={(val) =>
              saveSettings({ notify_on_complete: val })
            }
            trackColor={{ true: "#3B82F6" }}
          />
        </View>

        {settings?.notify_on_complete && (
          <>
            <Text style={styles.subLabel}>Method</Text>
            <View style={styles.chipRow}>
              {NOTIFY_METHODS.map((m) => (
                <TouchableOpacity
                  key={m.value}
                  style={[
                    styles.chip,
                    settings?.notification_method === m.value &&
                      styles.chipActive,
                  ]}
                  onPress={() =>
                    saveSettings({
                      notification_method: m.value as UserSettings["notification_method"],
                    })
                  }
                >
                  <Text
                    style={[
                      styles.chipText,
                      settings?.notification_method === m.value &&
                        styles.chipTextActive,
                    ]}
                  >
                    {m.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {(settings?.notification_method === "email" ||
              settings?.notification_method === "both") && (
              <View style={styles.inputGroup}>
                <Text style={styles.subLabel}>Email recipient</Text>
                <TextInput
                  style={styles.input}
                  value={settings?.email_recipient ?? ""}
                  onChangeText={(val) =>
                    setSettings((s) => s && { ...s, email_recipient: val })
                  }
                  onBlur={() =>
                    saveSettings({
                      email_recipient: settings?.email_recipient,
                    })
                  }
                  placeholder="email@example.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
            )}

            {(settings?.notification_method === "whatsapp" ||
              settings?.notification_method === "both") && (
              <View style={styles.inputGroup}>
                <Text style={styles.subLabel}>WhatsApp number</Text>
                <TextInput
                  style={styles.input}
                  value={settings?.whatsapp_recipient ?? ""}
                  onChangeText={(val) =>
                    setSettings((s) => s && { ...s, whatsapp_recipient: val })
                  }
                  onBlur={() =>
                    saveSettings({
                      whatsapp_recipient: settings?.whatsapp_recipient,
                    })
                  }
                  placeholder="+972501234567"
                  keyboardType="phone-pad"
                />
              </View>
            )}
          </>
        )}
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <FontAwesome name="sign-out" size={18} color="#EF4444" />
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>

      {saving && (
        <Text style={styles.savingText}>Saving...</Text>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  content: { padding: 16 },
  sectionHeader: {
    fontSize: 13,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 8,
    marginTop: 16,
  },
  card: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 4,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
  },
  switchRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 4,
  },
  label: { fontSize: 15, color: "#111827" },
  value: { fontSize: 15, color: "#6B7280" },
  planBadge: {
    fontSize: 13,
    fontWeight: "700",
    color: "#3B82F6",
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    overflow: "hidden",
  },
  subLabel: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 12,
    marginBottom: 6,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
  },
  chipActive: {
    backgroundColor: "#3B82F6",
  },
  chipText: {
    fontSize: 14,
    color: "#374151",
    fontWeight: "500",
  },
  chipTextActive: {
    color: "#FFF",
  },
  inputGroup: {
    marginTop: 4,
  },
  input: {
    height: 44,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
  },
  logoutButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#FEF2F2",
    borderRadius: 12,
    padding: 14,
    marginTop: 24,
  },
  logoutText: {
    fontSize: 16,
    color: "#EF4444",
    fontWeight: "600",
  },
  savingText: {
    textAlign: "center",
    fontSize: 13,
    color: "#9CA3AF",
    marginTop: 8,
  },
});
