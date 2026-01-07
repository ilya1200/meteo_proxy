"""Integration tests for /health endpoint."""

import pytest
from flask.testing import FlaskClient


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        """Health endpoint should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client: FlaskClient) -> None:
        """Health endpoint should return valid JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_contains_status(self, client: FlaskClient) -> None:
        """Health response should contain status field."""
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    def test_health_contains_version(self, client: FlaskClient) -> None:
        """Health response should contain version field."""
        response = client.get("/health")
        data = response.get_json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_contains_dependencies(self, client: FlaskClient) -> None:
        """Health response should contain dependencies field."""
        response = client.get("/health")
        data = response.get_json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], dict)
        # Should have redis and open_meteo dependencies
        assert "redis" in data["dependencies"]
        assert "open_meteo" in data["dependencies"]

    def test_health_contains_uptime(self, client: FlaskClient) -> None:
        """Health response should contain uptime_seconds field."""
        response = client.get("/health")
        data = response.get_json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_health_response_structure(self, client: FlaskClient) -> None:
        """Health response should have complete expected structure."""
        response = client.get("/health")
        data = response.get_json()

        expected_keys = {"status", "version", "dependencies", "uptime_seconds"}
        assert set(data.keys()) == expected_keys
