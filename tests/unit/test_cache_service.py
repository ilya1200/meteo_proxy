"""Unit tests for CacheService."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from weather_proxy.services.cache_service import CacheService


@pytest.mark.unit
class TestCacheService:
    """Tests for CacheService class."""

    def test_make_key_normalizes_input(self) -> None:
        """_make_key should normalize keys to lowercase and strip whitespace."""
        service = CacheService()

        assert service._make_key("Berlin") == "weather:berlin"
        assert service._make_key("BERLIN") == "weather:berlin"
        assert service._make_key("  Berlin  ") == "weather:berlin"
        assert service._make_key("New York") == "weather:new york"

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_returns_cached_data(self, mock_redis: Mock) -> None:
        """get should return cached data when found."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        cached_data = {"city": "Berlin", "temperature": 15.5}
        mock_client.get.return_value = json.dumps(cached_data)

        service = CacheService()
        result = service.get("Berlin")

        assert result == cached_data
        mock_client.get.assert_called_once_with("weather:berlin")

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_returns_none_when_not_found(self, mock_redis: Mock) -> None:
        """get should return None when key doesn't exist."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None

        service = CacheService()
        result = service.get("NonExistent")

        assert result is None

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_returns_none_on_redis_error(self, mock_redis: Mock) -> None:
        """get should return None on Redis errors."""
        import redis as redis_lib

        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.get.side_effect = redis_lib.RedisError("Connection failed")

        service = CacheService()
        result = service.get("Berlin")

        assert result is None

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_returns_none_on_invalid_json(self, mock_redis: Mock) -> None:
        """get should return None on corrupted JSON data."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = "invalid json{"

        service = CacheService()
        result = service.get("Berlin")

        assert result is None

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_set_stores_data_with_ttl(self, mock_redis: Mock) -> None:
        """set should store data with TTL."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        service = CacheService(ttl_seconds=300)
        data = {"city": "Berlin", "temperature": 15.5}
        result = service.set("Berlin", data)

        assert result is True
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        assert call_args[0][0] == "weather:berlin"
        assert call_args[0][1] == 300
        assert json.loads(call_args[0][2]) == data

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_set_uses_custom_ttl(self, mock_redis: Mock) -> None:
        """set should use custom TTL when provided."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        service = CacheService(ttl_seconds=300)
        data = {"city": "Berlin"}
        service.set("Berlin", data, ttl=600)

        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 600  # Custom TTL used

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_set_returns_false_on_redis_error(self, mock_redis: Mock) -> None:
        """set should return False on Redis errors."""
        import redis as redis_lib

        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.setex.side_effect = redis_lib.RedisError("Connection failed")

        service = CacheService()
        result = service.set("Berlin", {"city": "Berlin"})

        assert result is False

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_delete_removes_key(self, mock_redis: Mock) -> None:
        """delete should remove key from cache."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        service = CacheService()
        result = service.delete("Berlin")

        assert result is True
        mock_client.delete.assert_called_once_with("weather:berlin")

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_delete_returns_false_on_error(self, mock_redis: Mock) -> None:
        """delete should return False on Redis errors."""
        import redis as redis_lib

        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.delete.side_effect = redis_lib.RedisError("Connection failed")

        service = CacheService()
        result = service.delete("Berlin")

        assert result is False

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_ttl_returns_remaining_ttl(self, mock_redis: Mock) -> None:
        """get_ttl should return remaining TTL."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ttl.return_value = 245

        service = CacheService()
        result = service.get_ttl("Berlin")

        assert result == 245

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_get_ttl_returns_none_for_missing_key(self, mock_redis: Mock) -> None:
        """get_ttl should return None for missing keys."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ttl.return_value = -2  # Key doesn't exist

        service = CacheService()
        result = service.get_ttl("NonExistent")

        assert result is None

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_is_connected_returns_true(self, mock_redis: Mock) -> None:
        """is_connected should return True when Redis responds to ping."""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        service = CacheService()
        assert service.is_connected() is True

    @patch("weather_proxy.services.cache_service.redis.from_url")
    def test_is_connected_returns_false_on_error(self, mock_redis: Mock) -> None:
        """is_connected should return False when Redis is unreachable."""
        import redis as redis_lib

        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.side_effect = redis_lib.RedisError("Connection refused")

        service = CacheService()
        assert service.is_connected() is False

    def test_service_uses_default_config(self) -> None:
        """Service should use default config values."""
        service = CacheService()
        assert service.redis_url == "redis://localhost:6379/0"
        assert service.ttl_seconds == 300

    def test_service_uses_custom_config(self) -> None:
        """Service should use custom config when provided."""
        service = CacheService(
            redis_url="redis://custom:6380/1",
            ttl_seconds=600,
        )
        assert service.redis_url == "redis://custom:6380/1"
        assert service.ttl_seconds == 600
