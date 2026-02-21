/** API response types mirrored from backend Pydantic schemas. */

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: "free" | "pro" | "business";
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export type CallStatus =
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "summarizing"
  | "completed"
  | "failed";

export type UploadSource =
  | "manual"
  | "auto"
  | "api"
  | "mobile_auto"
  | "mobile_manual";

export interface Call {
  id: string;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  content_type: string;
  upload_source: UploadSource;
  contact_id: string | null;
  caller_phone: string | null;
  status: CallStatus;
  language_detected: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Summary {
  id: string;
  call_id: string;
  transcription_id: string;
  provider: string;
  model: string;
  summary_text: string;
  key_points: string[] | null;
  action_items: string[] | null;
  structured_actions: StructuredAction[] | null;
  participants_details: ParticipantDetail[] | null;
  topics: string[] | null;
  sentiment: string | null;
  language: string;
  tokens_used: number;
  status: string;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface StructuredAction {
  type: ActionType;
  description: string;
  details: Record<string, unknown>;
  confidence: number;
}

export type ActionType =
  | "calendar_event"
  | "send_email"
  | "send_whatsapp"
  | "reminder"
  | "task";

export interface ActionLink {
  type: ActionType;
  description: string;
  details: Record<string, unknown>;
  confidence: number;
  deep_link: string | null;
  link_type: "url" | "mailto" | "local";
}

export interface ParticipantDetail {
  speaker_label: string;
  name: string | null;
  role: string | null;
  phone: string | null;
}

export interface Transcription {
  id: string;
  call_id: string;
  text: string;
  confidence: number;
  language: string;
  speakers: SpeakerSegment[] | null;
  words_count: number;
  status: string;
}

export interface SpeakerSegment {
  speaker: string;
  text: string;
}

export interface CallDetail {
  call: Call;
  transcription: Transcription | null;
  summary: Summary | null;
}

export interface Contact {
  id: string;
  phone_number: string;
  name: string | null;
  company: string | null;
  email: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  summary_language: string;
  email_recipient: string | null;
  whatsapp_recipient: string | null;
  notify_on_complete: boolean;
  notification_method: "email" | "whatsapp" | "both" | "none";
  auto_upload_enabled: boolean;
}

export interface PresignResponse {
  upload_url: string;
  s3_key: string;
  s3_bucket: string;
  expires_in: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  actions?: ActionLink[];
  timestamp: string;
}
