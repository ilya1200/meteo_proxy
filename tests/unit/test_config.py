"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from weather_proxy.config import Config, get_config


@pytest.mark.unit
class TestConfig:
    """Tests for Config class."""

    def test_config_has_default_values(self) -> None:
        """Config should have sensible default values."""
        config = Config()

        assert config.flask_env == "production"
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.cache_ttl_seconds == 300
        assert config.open_meteo_base_url == "https://api.open-meteo.com"
        assert config.circuit_breaker_fail_max == 5
        assert config.circuit_breaker_reset_timeout == 60
        assert config.request_timeout_seconds == 10
        assert config.log_level == "INFO"

    def test_config_loads_from_environment(self) -> None:
        """Config should load values from environment variables."""
        env_vars = {
            "FLASK_ENV": "development",
            "REDIS_URL": "redis://custom:6380/1",
            "CACHE_TTL_SECONDS": "600",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = Config()

            assert config.flask_env == "development"
            assert config.redis_url == "redis://custom:6380/1"
            assert config.cache_ttl_seconds == 600
            assert config.log_level == "DEBUG"

    def test_config_debug_mode_in_development(self) -> None:
        """Debug mode should be enabled in development environment."""
        with patch.dict(os.environ, {"FLASK_ENV": "development"}, clear=False):
            config = Config()
            assert config.debug is True

    def test_config_debug_mode_disabled_in_production(self) -> None:
        """Debug mode should be disabled in production environment."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}, clear=False):
            config = Config()
            assert config.debug is False

    def test_get_config_returns_instance(self) -> None:
        """get_config should return a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_config_from_env_factory(self) -> None:
        """Config.from_env should create a valid Config instance."""
        config = Config.from_env()
        assert isinstance(config, Config)
        assert hasattr(config, "flask_env")
        assert hasattr(config, "redis_url")
