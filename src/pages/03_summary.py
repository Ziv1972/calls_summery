"""Summary page - view transcription and summary for a call."""

import json
import os
import sys

# Ensure project root is on path for src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import httpx

from src.utils.formatters import format_status_badge

API_BASE = "http://localhost:8001/api"


def _build_download_text(
    call_info: dict, summary: dict, transcription: dict | None
) -> str:
    """Build a plain-text download of the summary."""
    lines = []
    lines.append(f"Call: {call_info.get('original_filename', 'Unknown')}")
    lines.append(f"Date: {call_info.get('created_at', '')[:16]}")
    lines.append("")
    lines.append("=== SUMMARY ===")
    lines.append(summary.get("summary_text", ""))
    lines.append("")

    key_points = summary.get("key_points", [])
    if key_points:
        lines.append("=== KEY POINTS ===")
        for point in key_points:
            lines.append(f"- {point}")
        lines.append("")

    action_items = summary.get("action_items", [])
    if action_items:
        lines.append("=== ACTION ITEMS ===")
        for item in action_items:
            lines.append(f"- {item}")
        lines.append("")

    if transcription:
        speakers = transcription.get("speakers")
        if speakers:
            lines.append("=== CONVERSATION ===")
            for segment in speakers:
                speaker = segment.get("speaker", "Unknown")
                text = segment.get("text", "")
                lines.append(f"{speaker}: {text}")
            lines.append("")

        lines.append("=== FULL TRANSCRIPTION ===")
        lines.append(transcription.get("text", ""))

    return "\n".join(lines)


# RTL support for Hebrew content
st.markdown("""
<style>
    .rtl { direction: rtl; text-align: right; }
    div[data-testid="stMarkdown"] p,
    div[data-testid="stMarkdown"] li,
    div[data-testid="stMarkdown"] ul {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.header("Call Summary")

# Get call ID from session state or input
call_id = st.session_state.get("selected_call_id", "")
call_id_input = st.text_input("Call ID", value=call_id, help="Enter a call ID to view its summary")

if call_id_input:
    try:
        response = httpx.get(
            f"{API_BASE}/summaries/call/{call_id_input}",
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                detail = data["data"]
                call_info = detail.get("call", {})
                transcription = detail.get("transcription")
                summary = detail.get("summary")

                # Call info header
                st.subheader(call_info.get("original_filename", "Unknown"))
                st.caption(
                    f"Status: {format_status_badge(call_info.get('status', ''))} | "
                    f"Language: {call_info.get('language_detected', 'N/A')} | "
                    f"Created: {call_info.get('created_at', '')[:16]}"
                )

                # Summary section
                if summary:
                    st.markdown("---")
                    st.subheader("Summary")
                    st.markdown(summary.get("summary_text", "No summary available"))

                    # Key points
                    key_points = summary.get("key_points", [])
                    if key_points:
                        st.subheader("Key Points")
                        for point in key_points:
                            st.markdown(f"- {point}")

                    # Action items
                    action_items = summary.get("action_items", [])
                    if action_items:
                        st.subheader("Action Items")
                        for item in action_items:
                            st.markdown(f"- [ ] {item}")

                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sentiment", summary.get("sentiment", "N/A"))
                    with col2:
                        st.metric("Tokens Used", summary.get("tokens_used", 0))
                    with col3:
                        st.metric("Model", summary.get("model", "N/A"))

                    # Download summary
                    st.markdown("---")
                    download_text = _build_download_text(call_info, summary, transcription)
                    st.download_button(
                        label="Download Summary",
                        data=download_text,
                        file_name=f"summary_{call_id_input[:8]}.txt",
                        mime="text/plain",
                    )
                else:
                    st.info("Summary not yet available. Check back soon.")

                # Speaker conversation view
                if transcription:
                    speakers = transcription.get("speakers")
                    if speakers:
                        with st.expander("Speaker Conversation", expanded=True):
                            unique_speakers = sorted(set(s.get("speaker", "") for s in speakers))
                            st.caption(f"{len(unique_speakers)} speakers, {len(speakers)} segments")
                            for segment in speakers:
                                speaker = segment.get("speaker", "Unknown")
                                text = segment.get("text", "")
                                st.markdown(f"**{speaker}:** {text}")

                # Full transcription (collapsed)
                if transcription:
                    with st.expander("Full Transcription", expanded=False):
                        confidence = transcription.get("confidence", 0)
                        st.markdown(
                            f"**Confidence:** {confidence:.1%} | "
                            f"**Words:** {transcription.get('words_count', 0)}"
                        )
                        st.text_area(
                            "Transcription text",
                            value=transcription.get("text", ""),
                            height=300,
                            disabled=True,
                        )
            else:
                st.warning("No data found for this call.")
        elif response.status_code == 404:
            st.warning("Call not found. Please check the ID.")
        else:
            st.error(f"Error: HTTP {response.status_code}")

    except httpx.ConnectError:
        st.warning("Cannot connect to API server.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Enter a Call ID above or select a call from the Calls page.")
