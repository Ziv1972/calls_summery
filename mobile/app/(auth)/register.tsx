/** Register screen - name, email, password, link to login. */

import { Link, useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import { useAuthStore } from "@/src/stores/authStore";
import type { ApiResponse, AuthTokens, User } from "@/src/types/api";

export default function RegisterScreen() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { setTokens, setUser } = useAuthStore();
  const router = useRouter();

  const handleRegister = async () => {
    if (!email.trim() || !password || password.length < 8) {
      Alert.alert("Error", "Email and password (min 8 chars) are required");
      return;
    }

    setLoading(true);
    try {
      const { data: authRes } = await apiClient.post<ApiResponse<AuthTokens>>(
        "/auth/register",
        {
          email: email.trim().toLowerCase(),
          password,
          name: name.trim() || undefined,
        },
      );

      if (!authRes.data) throw new Error(authRes.error || "Registration failed");

      setTokens(authRes.data.access_token, authRes.data.refresh_token);

      const { data: meRes } = await apiClient.get<ApiResponse<User>>(
        "/auth/me",
      );
      if (meRes.data) setUser(meRes.data);

      router.replace("/(tabs)" as never);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Registration failed";
      Alert.alert("Registration Failed", message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.inner}>
        <Text style={styles.title}>Create Account</Text>
        <Text style={styles.subtitle}>Start summarizing your calls</Text>

        <TextInput
          style={styles.input}
          placeholder="Name (optional)"
          value={name}
          onChangeText={setName}
          autoCapitalize="words"
          autoComplete="name"
          textContentType="name"
        />

        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          textContentType="emailAddress"
        />

        <TextInput
          style={styles.input}
          placeholder="Password (min 8 characters)"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="new-password"
          textContentType="newPassword"
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleRegister}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Create Account</Text>
          )}
        </TouchableOpacity>

        <Link href="/(auth)/login" asChild>
          <TouchableOpacity style={styles.linkButton}>
            <Text style={styles.linkText}>
              Already have an account? <Text style={styles.linkBold}>Sign In</Text>
            </Text>
          </TouchableOpacity>
        </Link>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  inner: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#111827",
  },
  subtitle: {
    fontSize: 16,
    color: "#6B7280",
    marginBottom: 40,
  },
  input: {
    width: "100%",
    height: 50,
    backgroundColor: "#FFF",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    marginBottom: 12,
  },
  button: {
    width: "100%",
    height: 50,
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: "#FFF",
    fontSize: 17,
    fontWeight: "600",
  },
  linkButton: {
    marginTop: 24,
  },
  linkText: {
    fontSize: 15,
    color: "#6B7280",
  },
  linkBold: {
    color: "#3B82F6",
    fontWeight: "600",
  },
});
