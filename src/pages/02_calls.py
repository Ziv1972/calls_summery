"""Calls page - view all calls with status."""

import os
import sys
import time

# Ensure project root is on path for src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from src.utils import api_client
from src.utils.formatters import format_duration, format_file_size, format_status_badge

# Auth guard
if not st.session_state.get("access_token"):
    st.warning("Please log in to access this page.")
    st.stop()

st.header("Call History")

# Pagination
col1, col2 = st.columns([3, 1])
with col2:
    page = st.number_input("Page", min_value=1, value=1, step=1)

has_active_calls = False

try:
    response = api_client.get(
        "/calls/",
        params={"page": page, "page_size": 20},
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

                    # Retry button for failed calls
                    if status == "failed":
                        retry_col1, retry_col2 = st.columns(2)
                        with retry_col1:
                            retry_lang = st.selectbox(
                                "Retry language",
                                options=["he", "en", "auto"],
                                format_func=lambda x: {"he": "Hebrew", "en": "English", "auto": "Auto"}[x],
                                key=f"retry_lang_{call['id']}",
                            )
                        with retry_col2:
                            if st.button("Retry Processing", key=f"retry_{call['id']}", type="primary"):
                                retry_resp = api_client.post(
                                    f"/calls/{call['id']}/reprocess",
                                    params={"language": retry_lang},
                                )
                                if retry_resp.status_code == 200:
                                    st.success("Reprocessing started.")
                                    st.rerun()
                                else:
                                    error_data = retry_resp.json()
                                    st.error(f"Retry failed: {error_data.get('detail', retry_resp.status_code)}")

                    # Delete button with confirmation
                    confirm_key = f"confirm_delete_{call['id']}"
                    if st.session_state.get(confirm_key):
                        st.warning(f"Are you sure? This will permanently delete '{call['original_filename']}'.")
                        del_col1, del_col2 = st.columns(2)
                        with del_col1:
                            if st.button("Yes, delete", key=f"yes_del_{call['id']}", type="primary"):
                                del_resp = api_client.delete(f"/calls/{call['id']}")
                                if del_resp.status_code == 200:
                                    st.success("Call deleted.")
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                                else:
                                    st.error(f"Delete failed: HTTP {del_resp.status_code}")
                        with del_col2:
                            if st.button("Cancel", key=f"no_del_{call['id']}"):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                    else:
                        if st.button("Delete", key=f"del_{call['id']}"):
                            st.session_state[confirm_key] = True
                            st.rerun()

    else:
        st.error(f"Failed to load calls: HTTP {response.status_code}")

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
