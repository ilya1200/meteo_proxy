"""Cache service using Redis for storing weather data."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

import redis

from weather_proxy.config import get_config

if TYPE_CHECKING:
    from redis import Redis


class CacheServiceError(Exception):
    """Exception raised when cache operations fail."""

    pass


class CacheService:
    """
    Cache service for storing and retrieving weather data using Redis.

    Provides a simple key-value cache with TTL support.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL. Defaults to config.
            ttl_seconds: Default TTL for cached items in seconds. Defaults to config.
        """
        config = get_config()
        self.redis_url = redis_url or config.redis_url
        self.ttl_seconds = ttl_seconds or config.cache_ttl_seconds
        self._client: Redis[str] | None = None

    @property
    def client(self) -> Redis[str]:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._client

    def _make_key(self, key: str) -> str:
        """Generate a namespaced cache key."""
        return f"weather:{key.lower().strip()}"

    def get(self, key: str) -> dict[str, Any] | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key to retrieve (typically city name).

        Returns:
            Cached value as dict or None if not found or expired.
        """
        try:
            cache_key = self._make_key(key)
            data = self.client.get(cache_key)
            if data is None:
                return None
            return cast(dict[str, Any], json.loads(data))
        except redis.RedisError:
            # On Redis errors, return None to allow fresh fetch
            return None
        except json.JSONDecodeError:
            # On corrupted data, return None
            return None

    def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key (typically city name).
            value: Value to cache (must be JSON-serializable).
            ttl: Optional TTL override in seconds.

        Returns:
            True if successful, False otherwise.
        """
        try:
            cache_key = self._make_key(key)
            ttl_to_use = ttl if ttl is not None else self.ttl_seconds
            data = json.dumps(value)
            self.client.setex(cache_key, ttl_to_use, data)
            return True
        except redis.RedisError:
            return False
        except (TypeError, ValueError):
            # JSON serialization error
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            cache_key = self._make_key(key)
            self.client.delete(cache_key)
            return True
        except redis.RedisError:
            return False

    def get_ttl(self, key: str) -> int | None:
        """
        Get remaining TTL for a cached key.

        Args:
            key: Cache key.

        Returns:
            Remaining TTL in seconds, or None if key doesn't exist.
        """
        try:
            cache_key = self._make_key(key)
            ttl = self.client.ttl(cache_key)
            # Redis returns -2 if key doesn't exist, -1 if no TTL
            if ttl < 0:
                return None
            return ttl
        except redis.RedisError:
            return None

    def is_connected(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            True if connected, False otherwise.
        """
        try:
            self.client.ping()
            return True
        except redis.RedisError:
            return False

    def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
