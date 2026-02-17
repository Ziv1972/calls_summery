"""Upload page - upload and process call recordings."""

import os
import sys

# Ensure project root is on path for src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from src.utils import api_client

# Auth guard
if not st.session_state.get("access_token"):
    st.warning("Please log in to access this page.")
    st.stop()

st.header("Upload Call Recording")

# Plan usage info
try:
    usage_resp = api_client.get("/auth/usage")
    if usage_resp.status_code == 200:
        usage = usage_resp.json().get("data", {})
        plan = usage.get("plan", "free").upper()
        calls_this_month = usage.get("calls_this_month", 0)
        calls_limit = usage.get("calls_limit")
        max_mb = usage.get("max_file_size_mb", 500)

        if calls_limit is not None and calls_this_month >= calls_limit:
            st.error(
                f"You have reached your {plan} plan limit of {calls_limit} calls/month. "
                "Upgrade your plan to continue uploading."
            )
            st.stop()
        elif calls_limit is not None:
            st.info(f"Plan: {plan} | Calls: {calls_this_month}/{calls_limit} this month | Max file: {max_mb}MB")
        else:
            st.info(f"Plan: {plan} (unlimited) | Max file: {max_mb}MB")
except Exception:
    pass

# Language selection
language = st.selectbox(
    "Summary Language",
    options=["he", "en", "auto"],
    format_func=lambda x: {"auto": "Auto-detect (less reliable)", "he": "Hebrew", "en": "English"}[x],
    index=0,
)

# File upload
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["mp3", "mp4", "m4a", "wav", "ogg", "webm", "flac"],
    help="Supported formats: MP3, MP4, M4A, WAV, OGG, WebM, FLAC. Max 500MB.",
)

if uploaded_file is not None:
    st.audio(uploaded_file, format=uploaded_file.type)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**File:** {uploaded_file.name}")
    with col2:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.write(f"**Size:** {size_mb:.1f} MB")

    if st.button("Upload & Process", type="primary"):
        with st.spinner("Uploading to cloud..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                params = {"language": language, "upload_source": "manual"}

                response = api_client.post(
                    "/calls/upload",
                    files=files,
                    params=params,
                    timeout=120,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        call_data = data["data"]
                        st.success("Call uploaded successfully! Processing started.")
                        st.info(f"Call ID: `{call_data['id']}`")
                        st.info("Go to the **Calls** page to track progress.")
                    else:
                        st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
                else:
                    st.error(f"Upload failed: HTTP {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Upload failed: {e}")
