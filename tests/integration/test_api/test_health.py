"""Integration tests for health endpoint."""

import pytest


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check API."""

    async def test_health_returns_200(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "calls-summery"
