"""Notifications page - view notification history and retry failed."""

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

st.header("Notification History")

# Pagination
col1, col2 = st.columns([3, 1])
with col2:
    page = st.number_input("Page", min_value=1, value=1, step=1, key="notif_page")

try:
    response = api_client.get(
        "/notifications/",
        params={"page": page, "page_size": 20},
    )

    if response.status_code == 200:
        data = response.json()
        notifications = data.get("items", [])
        total = data.get("total", 0)

        st.caption(f"Total notifications: {total}")

        if not notifications:
            st.info("No notifications yet. Notifications are sent when call summaries complete.")
        else:
            for notif in notifications:
                status = notif["status"]
                delivery = notif["delivery_type"].upper()
                recipient = notif["recipient"]

                # Status badge
                if status == "sent":
                    badge = "Sent"
                elif status == "delivered":
                    badge = "Delivered"
                elif status == "failed":
                    badge = "Failed"
                else:
                    badge = status.capitalize()

                # Icon by delivery type
                icon = "email" if delivery == "EMAIL" else "smartphone"

                with st.expander(
                    f":{icon}: {delivery} | {badge} | {recipient} | {notif['created_at'][:16]}",
                    expanded=(status == "failed"),
                ):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Type:** {delivery}")
                        st.write(f"**To:** {recipient}")
                        st.write(f"**Status:** {badge}")
                    with col_b:
                        if notif.get("sent_at"):
                            st.write(f"**Sent at:** {notif['sent_at'][:19]}")
                        if notif.get("external_id"):
                            st.write(f"**Message ID:** `{notif['external_id']}`")

                    if notif.get("error_message"):
                        st.error(f"Error: {notif['error_message']}")

                    # Retry button for failed notifications
                    if status == "failed":
                        if st.button("Retry", key=f"retry_{notif['id']}"):
                            try:
                                retry_resp = api_client.post(
                                    f"/notifications/{notif['id']}/retry",
                                )
                                if retry_resp.status_code == 200:
                                    result = retry_resp.json()
                                    if result.get("success"):
                                        st.success("Notification resent successfully!")
                                    else:
                                        st.error(f"Retry failed: {result.get('error', 'Unknown error')}")
                                else:
                                    st.error(f"Retry failed: HTTP {retry_resp.status_code}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Retry error: {e}")

    else:
        st.error(f"Failed to load notifications: HTTP {response.status_code}")

except Exception as e:
    st.error(f"Error loading notifications: {e}")

# Refresh button
if st.button("Refresh", key="notif_refresh"):
    st.rerun()
