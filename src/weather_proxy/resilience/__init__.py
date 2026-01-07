"""Resilience patterns for fault tolerance."""

from weather_proxy.resilience.circuit_breaker import (
    CircuitBreakerOpen,
    get_geocoding_breaker,
    get_weather_breaker,
    with_retry,
)

__all__ = [
    "get_geocoding_breaker",
    "get_weather_breaker",
    "with_retry",
    "CircuitBreakerOpen",
]
