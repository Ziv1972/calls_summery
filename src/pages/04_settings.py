"""Settings page - configure language, notifications, auto-upload."""

import streamlit as st

st.header("⚙️ Settings")

st.info("Settings are stored locally in this session. Database-backed settings coming soon.")

# Language settings
st.subheader("Language")
summary_language = st.selectbox(
    "Default Summary Language",
    options=["auto", "he", "en"],
    format_func=lambda x: {"auto": "Auto-detect", "he": "Hebrew (עברית)", "en": "English"}[x],
    index=0,
    key="settings_language",
)

# Notification settings
st.subheader("Notifications")
notify_on_complete = st.checkbox("Send notification when summary is ready", value=True)

notification_method = st.selectbox(
    "Notification Method",
    options=["email", "whatsapp", "both", "none"],
    format_func=lambda x: {
        "email": "Email only",
        "whatsapp": "WhatsApp only",
        "both": "Both Email & WhatsApp",
        "none": "No notifications",
    }[x],
    index=0,
)

if notification_method in ("email", "both"):
    email_recipient = st.text_input(
        "Email Address",
        placeholder="your@email.com",
        key="settings_email",
    )

if notification_method in ("whatsapp", "both"):
    whatsapp_recipient = st.text_input(
        "WhatsApp Number (with country code)",
        placeholder="+972501234567",
        key="settings_whatsapp",
    )

# Auto-upload settings
st.subheader("Auto-Upload")
auto_upload = st.checkbox("Enable auto-upload from local agent", value=True)

if auto_upload:
    st.markdown("""
    #### Setup Instructions
    1. Install the local agent on your phone/PC
    2. Configure the watch folder in `agent/config.py`
    3. Run: `python agent/watcher.py`

    The agent will automatically upload new call recordings to the cloud.
    """)

# Save button (placeholder - will connect to DB)
st.markdown("---")
if st.button("💾 Save Settings", type="primary"):
    st.session_state["settings"] = {
        "summary_language": summary_language,
        "notify_on_complete": notify_on_complete,
        "notification_method": notification_method,
        "auto_upload_enabled": auto_upload,
    }
    st.success("Settings saved (session only)")
