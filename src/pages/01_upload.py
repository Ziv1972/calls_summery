"""Upload page - upload and process call recordings."""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000/api"

st.header("📤 Upload Call Recording")

# Language selection
language = st.selectbox(
    "Summary Language",
    options=["auto", "he", "en"],
    format_func=lambda x: {"auto": "Auto-detect", "he": "Hebrew (עברית)", "en": "English"}[x],
    index=0,
)

# File upload
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["mp3", "mp4", "m4a", "wav", "ogg", "webm"],
    help="Supported formats: MP3, MP4, M4A, WAV, OGG, WebM. Max 500MB.",
)

if uploaded_file is not None:
    st.audio(uploaded_file, format=uploaded_file.type)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**File:** {uploaded_file.name}")
    with col2:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.write(f"**Size:** {size_mb:.1f} MB")

    if st.button("🚀 Upload & Process", type="primary"):
        with st.spinner("Uploading to cloud..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                params = {"language": language, "upload_source": "manual"}

                response = httpx.post(
                    f"{API_BASE}/calls/upload",
                    files=files,
                    params=params,
                    timeout=120,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        call_data = data["data"]
                        st.success(f"Call uploaded successfully! Processing started.")
                        st.info(f"Call ID: `{call_data['id']}`")
                        st.info("Go to the **Calls** page to track progress.")
                    else:
                        st.error(f"Upload failed: {data.get('error', 'Unknown error')}")
                else:
                    st.error(f"Upload failed: HTTP {response.status_code} - {response.text}")

            except httpx.ConnectError:
                st.error("Cannot connect to API server. Make sure FastAPI is running on port 8000.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
