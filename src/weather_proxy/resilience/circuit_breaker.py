"""Circuit breaker and retry patterns for resilient external API calls."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import httpx
import pybreaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from weather_proxy.config import get_config

P = ParamSpec("P")
R = TypeVar("R")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    pass


# Circuit breakers for different external services
_geocoding_breaker: pybreaker.CircuitBreaker | None = None
_weather_breaker: pybreaker.CircuitBreaker | None = None


def get_geocoding_breaker() -> pybreaker.CircuitBreaker:
    """Get or create circuit breaker for geocoding service."""
    global _geocoding_breaker
    if _geocoding_breaker is None:
        config = get_config()
        _geocoding_breaker = pybreaker.CircuitBreaker(
            fail_max=config.circuit_breaker_fail_max,
            reset_timeout=config.circuit_breaker_reset_timeout,
            name="geocoding",
        )
    return _geocoding_breaker


def get_weather_breaker() -> pybreaker.CircuitBreaker:
    """Get or create circuit breaker for weather service."""
    global _weather_breaker
    if _weather_breaker is None:
        config = get_config()
        _weather_breaker = pybreaker.CircuitBreaker(
            fail_max=config.circuit_breaker_fail_max,
            reset_timeout=config.circuit_breaker_reset_timeout,
            name="weather",
        )
    return _weather_breaker


def with_retry(
    max_attempts: int | None = None,
    min_wait: float = 1,
    max_wait: float = 10,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to add retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts. Defaults to config.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.

    Returns:
        Decorated function with retry logic.
    """
    if max_attempts is None:
        config = get_config()
        max_attempts = config.retry_max_attempts

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(
                (
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.HTTPStatusError,
                )
            ),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_circuit_breaker(
    breaker: pybreaker.CircuitBreaker,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to wrap function with circuit breaker.

    Args:
        breaker: Circuit breaker instance to use.

    Returns:
        Decorated function with circuit breaker logic.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return breaker.call(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError as e:
                raise CircuitBreakerOpen(
                    f"Circuit breaker {breaker.name} is open"
                ) from e

        return wrapper

    return decorator


def reset_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    global _geocoding_breaker, _weather_breaker
    _geocoding_breaker = None
    _weather_breaker = None
