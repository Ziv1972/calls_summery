"""Summary page - view transcription and summary for a call."""

import streamlit as st
import httpx

from src.utils.formatters import format_status_badge

API_BASE = "http://localhost:8000/api"

st.header("📝 Call Summary")

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
                st.subheader(f"📞 {call_info.get('original_filename', 'Unknown')}")
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
                else:
                    st.info("Summary not yet available. Check back soon.")

                # Transcription section (collapsed by default)
                if transcription:
                    with st.expander("📄 Full Transcription", expanded=False):
                        st.markdown(f"**Confidence:** {transcription.get('confidence', 0):.1%}")
                        st.markdown(f"**Words:** {transcription.get('words_count', 0)}")
                        st.text_area(
                            "Transcription text",
                            value=transcription.get("text", ""),
                            height=300,
                            disabled=True,
                        )

                        # Speaker segments
                        speakers = transcription.get("speakers")
                        if speakers:
                            st.subheader("Speaker Segments")
                            for segment in speakers:
                                st.markdown(
                                    f"**{segment.get('speaker', 'Unknown')}:** {segment.get('text', '')}"
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
    st.info("Enter a Call ID above or select a call from the **Calls** page.")
