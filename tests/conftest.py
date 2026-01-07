"""Pytest configuration and fixtures."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from weather_proxy.app import create_app


@pytest.fixture
def app() -> Flask:
    """Create application for testing."""
    app = create_app(
        config_override={
            "TESTING": True,
            "DEBUG": False,
        }
    )
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_redis():
    """Mock Redis client for tests that don't need real Redis."""
    with patch("weather_proxy.services.cache_service.redis.from_url") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        # Default to cache miss
        mock_client.get.return_value = None
        mock_client.ping.return_value = True
        yield mock_client


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset cache service before each test."""
    from weather_proxy.routes.weather import reset_cache_service

    reset_cache_service()
    yield
    reset_cache_service()
