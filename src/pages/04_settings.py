"""Settings page - configure language, notifications, auto-upload."""

import streamlit as st
import httpx

API_BASE = "http://localhost:8001/api"

LANGUAGE_OPTIONS = {"auto": "Auto-detect", "he": "Hebrew (עברית)", "en": "English"}
METHOD_OPTIONS = {
    "email": "Email only",
    "whatsapp": "WhatsApp only",
    "both": "Both Email & WhatsApp",
    "none": "No notifications",
}


def _load_settings() -> dict:
    """Load settings from API."""
    try:
        response = httpx.get(f"{API_BASE}/settings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["data"]
    except httpx.ConnectError:
        st.warning("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error loading settings: {e}")
    return {}


def _save_settings(update: dict) -> bool:
    """Save settings via API."""
    try:
        response = httpx.put(f"{API_BASE}/settings", json=update, timeout=10)
        if response.status_code == 200:
            return True
        st.error(f"Failed to save: HTTP {response.status_code}")
    except httpx.ConnectError:
        st.error("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error saving settings: {e}")
    return False


st.header("Settings")

# Load current settings from DB
current = _load_settings()

if not current:
    st.info("Could not load settings. Make sure the API server is running.")
    st.stop()

# Language settings
st.subheader("Language")
language_keys = list(LANGUAGE_OPTIONS.keys())
current_lang = current.get("summary_language", "auto")
current_lang_idx = language_keys.index(current_lang) if current_lang in language_keys else 0

summary_language = st.selectbox(
    "Default Summary Language",
    options=language_keys,
    format_func=lambda x: LANGUAGE_OPTIONS[x],
    index=current_lang_idx,
    key="settings_language",
)

# Notification settings
st.subheader("Notifications")
notify_on_complete = st.checkbox(
    "Send notification when summary is ready",
    value=current.get("notify_on_complete", True),
)

method_keys = list(METHOD_OPTIONS.keys())
current_method = current.get("notification_method", "email")
current_method_idx = method_keys.index(current_method) if current_method in method_keys else 0

notification_method = st.selectbox(
    "Notification Method",
    options=method_keys,
    format_func=lambda x: METHOD_OPTIONS[x],
    index=current_method_idx,
)

email_recipient = current.get("email_recipient", "") or ""
whatsapp_recipient = current.get("whatsapp_recipient", "") or ""

if notification_method in ("email", "both"):
    email_recipient = st.text_input(
        "Email Address",
        value=email_recipient,
        placeholder="your@email.com",
        key="settings_email",
    )

if notification_method in ("whatsapp", "both"):
    whatsapp_recipient = st.text_input(
        "WhatsApp Number (with country code)",
        value=whatsapp_recipient,
        placeholder="+972501234567",
        key="settings_whatsapp",
    )

# Auto-upload settings
st.subheader("Auto-Upload")
auto_upload = st.checkbox(
    "Enable auto-upload from local agent",
    value=current.get("auto_upload_enabled", True),
)

if auto_upload:
    st.markdown("""
    #### Setup Instructions
    1. Place call recordings in the watch folder
    2. Run: `conda run -n calls_summery python -m agent.watcher`

    The agent will automatically upload new recordings to the cloud.
    """)

# Save button
st.markdown("---")
if st.button("Save Settings", type="primary"):
    update = {
        "summary_language": summary_language,
        "notify_on_complete": notify_on_complete,
        "notification_method": notification_method,
        "email_recipient": email_recipient,
        "whatsapp_recipient": whatsapp_recipient,
        "auto_upload_enabled": auto_upload,
    }
    if _save_settings(update):
        st.success("Settings saved successfully!")
        st.rerun()
