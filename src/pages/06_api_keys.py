"""API Key Management page - create, list, and revoke API keys."""

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

st.header("API Keys")
st.markdown("API keys let external tools (like the local agent) authenticate without a password.")

# Show newly created key (stored in session state until user confirms copy)
if st.session_state.get("new_api_key"):
    new_key_info = st.session_state["new_api_key"]
    st.success(f"Key **{new_key_info['name']}** created! Copy it now — it will not be shown again.")
    st.code(new_key_info["full_key"], language=None)
    if st.button("I've copied it"):
        del st.session_state["new_api_key"]
        st.rerun()
    st.markdown("---")

# Create new key
st.subheader("Create New Key")
with st.form("create_key_form"):
    key_name = st.text_input("Key Name", placeholder="e.g. Local Agent, CI Pipeline")
    create_submitted = st.form_submit_button("Generate Key", type="primary")

if create_submitted:
    if not key_name.strip():
        st.error("Key name is required.")
    else:
        try:
            create_resp = api_client.post("/api-keys/", json={"name": key_name.strip()})
            if create_resp.status_code == 201:
                created = create_resp.json().get("data", {})
                st.session_state["new_api_key"] = created
                st.rerun()
            else:
                st.error(f"Failed to create key: HTTP {create_resp.status_code}")
        except Exception as e:
            st.error(f"Error creating key: {e}")

# List existing keys
st.markdown("---")
st.subheader("Existing Keys")

try:
    response = api_client.get("/api-keys/")
    if response.status_code == 200:
        data = response.json()
        keys = data.get("data", []) or []

        if not keys:
            st.info("No API keys yet. Create one above.")
        else:
            for key in keys:
                col_a, col_b, col_c = st.columns([3, 2, 1])
                with col_a:
                    active_label = "" if key.get("is_active", True) else " (revoked)"
                    st.write(f"**{key['name']}**{active_label}")
                    st.caption(f"Prefix: `{key['key_prefix']}...`")
                with col_b:
                    last_used = key.get("last_used_at")
                    st.caption(f"Last used: {last_used[:16] if last_used else 'Never'}")
                    st.caption(f"Created: {key['created_at'][:16]}")
                with col_c:
                    if key.get("is_active", True):
                        if st.button("Revoke", key=f"revoke_{key['id']}"):
                            try:
                                del_resp = api_client.delete(f"/api-keys/{key['id']}")
                                if del_resp.status_code == 200:
                                    st.success(f"Key '{key['name']}' revoked.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to revoke: HTTP {del_resp.status_code}")
                            except Exception as e:
                                st.error(f"Error revoking key: {e}")
    else:
        st.error(f"Failed to load keys: HTTP {response.status_code}")
except Exception as e:
    st.error(f"Error loading API keys: {e}")
