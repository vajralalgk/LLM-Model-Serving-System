"""
Tests for the POST /rank API endpoint.
Validates request/response schemas, authentication, and ranking behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the lru_cache on get_settings before each test."""
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_app():
    """Create a test application with mocked model components."""
    import os
    os.environ["APP_ENV"] = "test"
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    os.environ["API_KEY"] = "test-api-key"
    os.environ["MODEL_DEVICE"] = "cpu"
    os.environ["ENABLE_TRACING"] = "false"

    # Re-import to pick up new env vars
    from app.config import get_settings
    get_settings.cache_clear()

    from app.main import create_app
    app = create_app()

    # Mock the application state
    mock_registry = MagicMock()
    mock_registry.list_versions.return_value = ["v1"]
    mock_registry.active_version = "v1"

    mock_server = MagicMock()
    mock_server.is_ready.return_value = True
    mock_server.current_version = "v1"

    mock_batcher = MagicMock()
    mock_batcher.is_running.return_value = True
    mock_batcher.queue_size = 0
    mock_batcher.submit = AsyncMock(return_value=[0.95, 0.82, 0.67])

    mock_metrics = MagicMock()

    app.state.model_registry = mock_registry
    app.state.model_server = mock_server
    app.state.dynamic_batcher = mock_batcher
    app.state.metrics = mock_metrics

    yield app

    # Cleanup env vars
    for key in ["APP_ENV", "JWT_SECRET_KEY", "API_KEY", "MODEL_DEVICE", "ENABLE_TRACING"]:
        os.environ.pop(key, None)


@pytest.fixture
def client(mock_app):
    return TestClient(mock_app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-api-key"}


class TestRankEndpoint:
    """Tests for POST /rank endpoint."""

    def test_rank_success(self, client, auth_headers):
        """Test successful ranking request."""
        response = client.post(
            "/rank",
            json={
                "user_id": "user_123",
                "context": {"location": "US", "device": "mobile"},
                "candidate_titles": [
                    "Breaking News: AI Advances",
                    "Sports Update",
                    "Weather Forecast",
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "ranked_titles" in data
        assert "model_version" in data
        assert "request_id" in data
        assert "latency_ms" in data
        assert len(data["ranked_titles"]) == 3

    def test_rank_missing_auth(self, client):
        """Test request without authentication."""
        response = client.post(
            "/rank",
            json={
                "user_id": "user_123",
                "context": {},
                "candidate_titles": ["Title 1"],
            },
        )
        assert response.status_code == 401

    def test_rank_invalid_payload(self, client, auth_headers):
        """Test request with invalid payload."""
        response = client.post(
            "/rank",
            json={"user_id": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_rank_empty_titles(self, client, auth_headers):
        """Test request with empty candidate titles list."""
        response = client.post(
            "/rank",
            json={
                "user_id": "user_123",
                "context": {},
                "candidate_titles": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_rank_with_model_version(self, client, auth_headers):
        """Test request with explicit model version."""
        response = client.post(
            "/rank",
            json={
                "user_id": "user_123",
                "context": {},
                "candidate_titles": ["Title A", "Title B"],
                "model_version": "v1",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_liveness(self, client):
        """Test liveness probe."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness(self, client):
        """Test readiness probe."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_version(self, client):
        """Test version endpoint."""
        response = client.get("/version")
        assert response.status_code == 200
        assert "service_version" in response.json()

    def test_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
