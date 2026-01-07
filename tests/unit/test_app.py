"""Unit tests for Flask application factory."""

import pytest
from flask import Flask

from weather_proxy.app import create_app, get_uptime_seconds


@pytest.mark.unit
class TestAppFactory:
    """Tests for create_app factory function."""

    def test_create_app_returns_flask_instance(self) -> None:
        """create_app should return a Flask application."""
        app = create_app()
        assert isinstance(app, Flask)

    def test_create_app_has_health_route(self) -> None:
        """Application should have /health route registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/health" in rules

    def test_create_app_has_weather_route(self) -> None:
        """Application should have /weather route registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/weather" in rules

    def test_create_app_with_config_override(self) -> None:
        """create_app should accept configuration overrides."""
        app = create_app(config_override={"TESTING": True, "CUSTOM_VALUE": "test"})
        assert app.config["TESTING"] is True
        assert app.config["CUSTOM_VALUE"] == "test"

    def test_create_app_stores_version(self) -> None:
        """Application should store version in config."""
        app = create_app()
        assert "APP_VERSION" in app.config
        assert app.config["APP_VERSION"] == "1.0.0"

    def test_create_app_stores_app_config(self) -> None:
        """Application should store app config in Flask config."""
        app = create_app()
        assert "APP_CONFIG" in app.config
        assert hasattr(app.config["APP_CONFIG"], "redis_url")


@pytest.mark.unit
class TestUptime:
    """Tests for uptime tracking."""

    def test_get_uptime_returns_positive_number(self) -> None:
        """get_uptime_seconds should return a positive number."""
        uptime = get_uptime_seconds()
        assert isinstance(uptime, float)
        assert uptime >= 0

    def test_get_uptime_increases(self) -> None:
        """Uptime should increase over time."""
        import time

        uptime1 = get_uptime_seconds()
        time.sleep(0.1)
        uptime2 = get_uptime_seconds()
        assert uptime2 > uptime1
