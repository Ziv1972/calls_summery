"""Shared API client for Streamlit pages.

Wraps httpx with automatic Authorization header injection from
st.session_state and 401 handling.
"""

import os

import httpx
import streamlit as st

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8001/api")


def _get_headers() -> dict[str, str]:
    """Build auth headers from session state."""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(response: httpx.Response) -> httpx.Response:
    """Handle 401 by clearing session and stopping the page."""
    if response.status_code == 401:
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.session_state.pop("user", None)
        st.error("Session expired. Please log in again.")
        st.stop()
    return response


def get(path: str, *, params: dict | None = None, timeout: float = 10) -> httpx.Response:
    """GET request with auth headers."""
    response = httpx.get(
        f"{API_BASE}{path}",
        headers=_get_headers(),
        params=params,
        timeout=timeout,
    )
    return _handle_response(response)


def post(
    path: str,
    *,
    json: dict | None = None,
    files: dict | None = None,
    data: dict | None = None,
    params: dict | None = None,
    timeout: float = 30,
) -> httpx.Response:
    """POST request with auth headers."""
    response = httpx.post(
        f"{API_BASE}{path}",
        headers=_get_headers(),
        json=json,
        files=files,
        data=data,
        params=params,
        timeout=timeout,
    )
    return _handle_response(response)


def put(path: str, *, json: dict | None = None, timeout: float = 10) -> httpx.Response:
    """PUT request with auth headers."""
    response = httpx.put(
        f"{API_BASE}{path}",
        headers=_get_headers(),
        json=json,
        timeout=timeout,
    )
    return _handle_response(response)


def delete(path: str, *, timeout: float = 10) -> httpx.Response:
    """DELETE request with auth headers."""
    response = httpx.delete(
        f"{API_BASE}{path}",
        headers=_get_headers(),
        timeout=timeout,
    )
    return _handle_response(response)
