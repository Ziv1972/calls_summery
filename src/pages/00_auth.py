"""Authentication page - login and registration."""

import os
import sys

# Ensure project root is on path for src imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import httpx

from src.utils.api_client import API_BASE

st.header("Sign In")

# If already logged in, show status and option to logout
if st.session_state.get("access_token"):
    user = st.session_state.get("user", {})
    st.success(f"Logged in as **{user.get('email', 'Unknown')}**")
    if st.button("Log Out"):
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.session_state.pop("user", None)
        st.rerun()
    st.stop()

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary")

    if submitted:
        if not email or not password:
            st.error("Email and password are required.")
        else:
            try:
                response = httpx.post(
                    f"{API_BASE}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        token_data = data["data"]
                        st.session_state["access_token"] = token_data["access_token"]
                        st.session_state["refresh_token"] = token_data["refresh_token"]
                        # Fetch user profile
                        me_resp = httpx.get(
                            f"{API_BASE}/auth/me",
                            headers={"Authorization": f"Bearer {token_data['access_token']}"},
                            timeout=10,
                        )
                        if me_resp.status_code == 200:
                            me_data = me_resp.json()
                            st.session_state["user"] = me_data.get("data", {})
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error(data.get("error", "Login failed."))
                elif response.status_code == 401:
                    st.error("Invalid email or password.")
                else:
                    st.error(f"Login failed: HTTP {response.status_code}")
            except httpx.ConnectError:
                st.error("Cannot connect to API server. Make sure FastAPI is running on port 8001.")
            except Exception as e:
                st.error(f"Login error: {e}")

with tab_register:
    with st.form("register_form"):
        reg_name = st.text_input("Full Name (optional)")
        reg_email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
        reg_password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
        reg_submitted = st.form_submit_button("Create Account", type="primary")

    if reg_submitted:
        if not reg_email or not reg_password:
            st.error("Email and password are required.")
        elif len(reg_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                body = {"email": reg_email, "password": reg_password}
                if reg_name:
                    body["full_name"] = reg_name
                response = httpx.post(
                    f"{API_BASE}/auth/register",
                    json=body,
                    timeout=10,
                )
                if response.status_code == 201:
                    data = response.json()
                    if data.get("success"):
                        st.success("Account created! Please log in using the Login tab.")
                    else:
                        st.error(data.get("error", "Registration failed."))
                elif response.status_code == 409:
                    st.error("Email already registered. Please log in instead.")
                else:
                    st.error(f"Registration failed: HTTP {response.status_code}")
            except httpx.ConnectError:
                st.error("Cannot connect to API server.")
            except Exception as e:
                st.error(f"Registration error: {e}")
