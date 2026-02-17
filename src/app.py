"""Streamlit app entry point."""

import streamlit as st

st.set_page_config(
    page_title="Calls Summary",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📞 Calls Summary")
st.markdown("Upload phone call recordings, get AI-powered transcriptions and summaries.")

st.markdown("---")
st.markdown("""
### How it works
1. **Upload** a call recording (or enable auto-upload from your phone)
2. **Transcribe** - Deepgram Nova-3 auto-detects the language and transcribes
3. **Summarize** - Claude AI generates a structured summary
4. **Deliver** - Get the summary via email or WhatsApp

### Navigate
Use the sidebar to navigate between pages:
- **Upload** - Upload and process new calls
- **Calls** - View all calls and their status
- **Summary** - View transcriptions and summaries
- **Settings** - Configure language, notifications, auto-upload
""")

# Sidebar: logged-in user display
if st.session_state.get("user"):
    user = st.session_state["user"]
    st.sidebar.markdown(f"**{user.get('full_name') or user.get('email', 'User')}**")
    st.sidebar.caption(user.get("email", ""))
    if st.sidebar.button("Log Out", key="sidebar_logout"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.session_state.pop("user", None)
        st.rerun()
    st.sidebar.markdown("---")

# API health check
API_BASE = "http://localhost:8001/api"

try:
    import httpx

    response = httpx.get(f"{API_BASE}/health", timeout=2)
    if response.status_code == 200:
        st.sidebar.success("API: Connected")
    else:
        st.sidebar.error("API: Error")
except Exception:
    st.sidebar.warning("API: Not available (start FastAPI server)")
