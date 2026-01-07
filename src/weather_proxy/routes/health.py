"""Health check endpoint."""

from typing import Any

from flask import Blueprint, current_app, jsonify

from weather_proxy.app import get_uptime_seconds
from weather_proxy.services.cache_service import CacheService
from weather_proxy.services.weather_service import WeatherService

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check() -> tuple[Any, int]:
    """
    Health check endpoint.

    Returns service health status, version, and dependency states.

    Returns:
        JSON response with health information and HTTP 200.
    """
    version = current_app.config.get("APP_VERSION", "unknown")

    # Check dependencies
    dependencies = {
        "redis": _check_redis_health(),
        "open_meteo": _check_open_meteo_health(),
    }

    # Determine overall status
    all_healthy = all(
        status in ("connected", "available", "not_configured")
        for status in dependencies.values()
    )
    status = "healthy" if all_healthy else "degraded"

    response = {
        "status": status,
        "version": version,
        "dependencies": dependencies,
        "uptime_seconds": round(get_uptime_seconds(), 2),
    }

    return jsonify(response), 200


def _check_redis_health() -> str:
    """
    Check Redis connection health.

    Returns:
        'connected' if healthy, 'disconnected' otherwise.
    """
    try:
        cache_service = CacheService()
        if cache_service.is_connected():
            return "connected"
        return "disconnected"
    except Exception:
        return "disconnected"


def _check_open_meteo_health() -> str:
    """
    Check Open-Meteo API availability.

    Returns:
        'available' if reachable, 'unavailable' otherwise.
    """
    try:
        weather_service = WeatherService()
        if weather_service.is_available():
            return "available"
        return "unavailable"
    except Exception:
        return "unavailable"
