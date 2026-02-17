"""Unit tests for the shared Streamlit API client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest


class TestGetHeaders:
    """Test header building from session state."""

    @patch("streamlit.session_state", {})
    def test_no_token_returns_empty_headers(self):
        from src.utils.api_client import _get_headers

        assert _get_headers() == {}

    @patch("streamlit.session_state", {"access_token": "test-token-123"})
    def test_with_token_returns_bearer_header(self):
        from src.utils.api_client import _get_headers

        headers = _get_headers()
        assert headers == {"Authorization": "Bearer test-token-123"}


class TestHandleResponse:
    """Test 401 handling."""

    @patch("streamlit.session_state", {})
    def test_non_401_returns_response(self):
        from src.utils.api_client import _handle_response

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        result = _handle_response(mock_response)
        assert result is mock_response

    @patch("streamlit.session_state", {"access_token": "old", "refresh_token": "old", "user": {}})
    @patch("streamlit.stop", side_effect=Exception("stop"))
    @patch("streamlit.error")
    def test_401_clears_auth_and_stops(self, mock_error, mock_stop):
        from src.utils.api_client import _handle_response

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        with pytest.raises(Exception, match="stop"):
            _handle_response(mock_response)

        mock_error.assert_called_once()
        mock_stop.assert_called_once()

    @patch("streamlit.session_state", {"access_token": "old", "refresh_token": "old", "user": {}})
    @patch("streamlit.stop", side_effect=Exception("stop"))
    @patch("streamlit.error")
    def test_401_removes_tokens_from_session(self, mock_error, mock_stop):
        import streamlit as st

        from src.utils.api_client import _handle_response

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401

        with pytest.raises(Exception, match="stop"):
            _handle_response(mock_response)

        assert "access_token" not in st.session_state
        assert "refresh_token" not in st.session_state
        assert "user" not in st.session_state
