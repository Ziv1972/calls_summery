/** Upload screen - document picker, presign, S3 PUT, webhook. */

import { FontAwesome } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import { useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import apiClient from "@/src/api/client";
import type { ApiResponse, PresignResponse } from "@/src/types/api";
import { formatFileSize } from "@/src/utils/formatters";

interface PickedFile {
  uri: string;
  name: string;
  size: number;
  mimeType: string;
}

export default function UploadScreen() {
  const router = useRouter();
  const [file, setFile] = useState<PickedFile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState("");

  const pickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["audio/*"],
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets?.[0]) return;

      const asset = result.assets[0];
      setFile({
        uri: asset.uri,
        name: asset.name,
        size: asset.size ?? 0,
        mimeType: asset.mimeType ?? "audio/mpeg",
      });
    } catch {
      Alert.alert("Error", "Failed to pick file");
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    setUploading(true);

    try {
      // Step 1: Get presigned URL
      setProgress("Getting upload URL...");
      const { data: presignRes } = await apiClient.post<
        ApiResponse<PresignResponse>
      >("/uploads/presign", {
        filename: file.name,
        content_type: file.mimeType,
        file_size_bytes: file.size,
      });

      if (!presignRes.data) {
        throw new Error(presignRes.error || "Failed to get upload URL");
      }

      const { upload_url, s3_key, s3_bucket } = presignRes.data;

      // Step 2: Upload to S3 via presigned PUT URL
      setProgress("Uploading to cloud...");
      const fileResponse = await fetch(file.uri);
      const blob = await fileResponse.blob();
      const s3Response = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.mimeType },
        body: blob,
      });

      if (!s3Response.ok) {
        throw new Error(`S3 upload failed with status ${s3Response.status}`);
      }

      // Step 3: Notify backend via webhook
      setProgress("Processing...");
      const { data: webhookRes } = await apiClient.post("/webhooks/s3-upload", {
        bucket: s3_bucket,
        key: s3_key,
        size: file.size,
        content_type: file.mimeType,
        original_filename: file.name,
        upload_source: "mobile_manual",
      });

      const callId = webhookRes.data?.call_id || webhookRes.call_id;

      Alert.alert("Upload Complete", "Your call is being processed.", [
        {
          text: "View Call",
          onPress: () => {
            if (callId) {
              router.push(`/(tabs)/calls/${callId}` as never);
            } else {
              router.push("/(tabs)/calls" as never);
            }
          },
        },
        { text: "OK" },
      ]);

      setFile(null);
      setProgress("");
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ||
        (err as Error)?.message ||
        "Upload failed";
      Alert.alert("Upload Failed", message);
      setProgress("");
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.inner}>
        <FontAwesome name="cloud-upload" size={56} color="#3B82F6" />
        <Text style={styles.title}>Upload Call Recording</Text>
        <Text style={styles.subtitle}>
          Select an audio file from your device
        </Text>

        {!file ? (
          <TouchableOpacity style={styles.pickButton} onPress={pickFile}>
            <FontAwesome name="folder-open" size={20} color="#3B82F6" />
            <Text style={styles.pickButtonText}>Choose Audio File</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.fileCard}>
            <FontAwesome name="file-audio-o" size={24} color="#3B82F6" />
            <View style={styles.fileInfo}>
              <Text style={styles.fileName} numberOfLines={1}>
                {file.name}
              </Text>
              <Text style={styles.fileMeta}>{formatFileSize(file.size)}</Text>
            </View>
            <TouchableOpacity onPress={() => setFile(null)}>
              <FontAwesome name="times" size={18} color="#9CA3AF" />
            </TouchableOpacity>
          </View>
        )}

        {file && (
          <TouchableOpacity
            style={[styles.uploadButton, uploading && styles.buttonDisabled]}
            onPress={uploadFile}
            disabled={uploading}
          >
            {uploading ? (
              <View style={styles.uploadingRow}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.uploadButtonText}>{progress}</Text>
              </View>
            ) : (
              <Text style={styles.uploadButtonText}>Upload & Process</Text>
            )}
          </TouchableOpacity>
        )}

        <View style={styles.formatInfo}>
          <Text style={styles.formatTitle}>Supported formats</Text>
          <Text style={styles.formatText}>
            MP3, M4A, WAV, OGG, WebM, FLAC, AAC
          </Text>
          <Text style={styles.formatText}>Max 500MB per file</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  inner: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
    marginTop: 16,
  },
  subtitle: {
    fontSize: 15,
    color: "#6B7280",
    marginBottom: 32,
  },
  pickButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#BFDBFE",
    borderStyle: "dashed",
  },
  pickButtonText: {
    fontSize: 16,
    color: "#3B82F6",
    fontWeight: "600",
  },
  fileCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: "#FFF",
    padding: 14,
    borderRadius: 12,
    width: "100%",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  fileInfo: { flex: 1 },
  fileName: { fontSize: 15, fontWeight: "600", color: "#111827" },
  fileMeta: { fontSize: 13, color: "#6B7280", marginTop: 2 },
  uploadButton: {
    width: "100%",
    height: 50,
    backgroundColor: "#3B82F6",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 16,
  },
  buttonDisabled: { opacity: 0.7 },
  uploadButtonText: { color: "#FFF", fontSize: 16, fontWeight: "600" },
  uploadingRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  formatInfo: {
    alignItems: "center",
    marginTop: 40,
    gap: 4,
  },
  formatTitle: { fontSize: 13, fontWeight: "600", color: "#9CA3AF" },
  formatText: { fontSize: 13, color: "#D1D5DB" },
});
