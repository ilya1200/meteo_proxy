"""Prometheus metrics for monitoring."""

from flask import Blueprint, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Info,
    generate_latest,
)

# Metrics
REQUEST_COUNT = Counter(
    "weather_requests_total",
    "Total number of weather requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "weather_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

CACHE_HITS = Counter("weather_cache_hits_total", "Total number of cache hits")

CACHE_MISSES = Counter("weather_cache_misses_total", "Total number of cache misses")

EXTERNAL_API_CALLS = Counter(
    "weather_external_api_calls_total",
    "Total number of external API calls",
    ["service", "status"],
)

CIRCUIT_BREAKER_STATE = Counter(
    "weather_circuit_breaker_state_changes_total",
    "Circuit breaker state changes",
    ["service", "state"],
)

APP_INFO = Info("weather_proxy", "Weather Proxy Service information")


def init_metrics(version: str) -> None:
    """Initialize application metrics with version info."""
    APP_INFO.info({"version": version})


def record_request(method: str, endpoint: str, status: str, duration: float) -> None:
    """Record a request metric."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_cache_hit() -> None:
    """Record a cache hit."""
    CACHE_HITS.inc()


def record_cache_miss() -> None:
    """Record a cache miss."""
    CACHE_MISSES.inc()


def record_external_call(service: str, status: str) -> None:
    """Record an external API call."""
    EXTERNAL_API_CALLS.labels(service=service, status=status).inc()


# Metrics blueprint
metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
