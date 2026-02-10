"""Calls page - view all calls with status."""

import time

import streamlit as st
import httpx

from src.utils.formatters import format_duration, format_file_size, format_status_badge

API_BASE = "http://localhost:8001/api"

st.header("Call History")

# Pagination
col1, col2 = st.columns([3, 1])
with col2:
    page = st.number_input("Page", min_value=1, value=1, step=1)

has_active_calls = False

try:
    response = httpx.get(
        f"{API_BASE}/calls/",
        params={"page": page, "page_size": 20},
        timeout=10,
    )

    if response.status_code == 200:
        data = response.json()
        calls = data.get("items", [])
        total = data.get("total", 0)

        st.caption(f"Total calls: {total}")

        if not calls:
            st.info("No calls yet. Go to **Upload** to add your first call.")
        else:
            for call in calls:
                status = call["status"]
                is_processing = status in ("uploaded", "transcribing", "transcribed", "summarizing")
                if is_processing:
                    has_active_calls = True

                with st.expander(
                    f"{format_status_badge(status)} | "
                    f"{call['original_filename']} | "
                    f"{call['created_at'][:16]}",
                    expanded=is_processing,
                ):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.write(f"**Status:** {format_status_badge(status)}")
                        st.write(f"**Source:** {call['upload_source']}")
                    with col_b:
                        st.write(f"**Duration:** {format_duration(call.get('duration_seconds'))}")
                        st.write(f"**Size:** {format_file_size(call['file_size_bytes'])}")
                    with col_c:
                        st.write(f"**Language:** {call.get('language_detected') or 'Detecting...'}")
                        if call.get("error_message"):
                            st.error(call["error_message"])

                    # View summary button
                    if status == "completed":
                        if st.button("View Summary", key=f"view_{call['id']}"):
                            st.session_state["selected_call_id"] = call["id"]
                            st.switch_page("pages/03_summary.py")

    else:
        st.error(f"Failed to load calls: HTTP {response.status_code}")

except httpx.ConnectError:
    st.warning("Cannot connect to API server. Make sure FastAPI is running on port 8001.")
except Exception as e:
    st.error(f"Error loading calls: {e}")

# Manual refresh button
col_r1, col_r2 = st.columns([1, 3])
with col_r1:
    if st.button("Refresh"):
        st.rerun()

# Auto-refresh when calls are being processed
if has_active_calls:
    with col_r2:
        st.info("Processing in progress... auto-refreshing every 8 seconds")
    time.sleep(8)
    st.rerun()
