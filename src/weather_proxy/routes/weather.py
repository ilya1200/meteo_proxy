"""Weather endpoint for retrieving weather data by city."""

import contextlib
import uuid
from typing import Any

from flask import Blueprint, g, jsonify, request

from weather_proxy.services.cache_service import CacheService
from weather_proxy.services.geocoding_service import (
    CityNotFoundError,
    GeocodingError,
    GeocodingService,
)
from weather_proxy.services.weather_service import (
    WeatherService,
    WeatherServiceError,
)

weather_bp = Blueprint("weather", __name__)

# Module-level cache service instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_request_id() -> str:
    """Get or generate a request ID for correlation."""
    if hasattr(g, "request_id"):
        return g.request_id
    g.request_id = str(uuid.uuid4())
    return g.request_id


def _build_weather_response(
    city: str,
    country: str | None,
    latitude: float,
    longitude: float,
    weather_data: dict[str, Any],
    cached: bool,
    cache_ttl: int | None,
    request_id: str,
) -> dict[str, Any]:
    """Build standardized weather response."""
    response = {
        "city": city,
        "country": country,
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "current": weather_data,
        "cached": cached,
        "request_id": request_id,
    }

    if cache_ttl is not None:
        response["cache_expires_in"] = cache_ttl

    return response


@weather_bp.route("/weather", methods=["GET"])
def get_weather() -> tuple[Any, int]:
    """
    Get weather data for a city.

    Query Parameters:
        city: Name of the city to get weather for (required).

    Returns:
        JSON response with weather data or error message.

    Response Codes:
        200: Success - weather data returned
        400: Bad Request - missing or invalid city parameter
        404: Not Found - city not found
        502: Bad Gateway - external API error
        503: Service Unavailable - service temporarily unavailable
    """
    request_id = get_request_id()

    # Validate city parameter
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify(
            {
                "error": {
                    "code": "MISSING_PARAMETER",
                    "message": "Missing required parameter: city",
                    "request_id": request_id,
                }
            }
        ), 400

    # Validate city name length
    if len(city) > 100:
        return jsonify(
            {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "City name too long (max 100 characters)",
                    "request_id": request_id,
                }
            }
        ), 400

    try:
        # Try to get from cache first
        cache_service = get_cache_service()
        cache_key = city.lower()

        cached_data = None
        with contextlib.suppress(Exception):
            cached_data = cache_service.get(cache_key)

        if cached_data is not None:
            # Cache hit - return cached data
            cache_ttl = cache_service.get_ttl(cache_key)
            return jsonify(
                _build_weather_response(
                    city=cached_data.get("city", city),
                    country=cached_data.get("country"),
                    latitude=cached_data["coordinates"]["latitude"],
                    longitude=cached_data["coordinates"]["longitude"],
                    weather_data=cached_data["current"],
                    cached=True,
                    cache_ttl=cache_ttl,
                    request_id=request_id,
                )
            ), 200

        # Cache miss - fetch fresh data
        # Step 1: Geocode city to coordinates
        geocoding_service = GeocodingService()
        coords = geocoding_service.city_to_coords(city)

        # Step 2: Fetch weather data
        weather_service = WeatherService()
        weather = weather_service.get_weather(coords.latitude, coords.longitude)

        # Build weather data dict
        weather_data = {
            "temperature": weather.temperature,
            "temperature_unit": weather.temperature_unit,
            "apparent_temperature": weather.apparent_temperature,
            "humidity": weather.humidity,
            "weather_code": weather.weather_code,
            "weather_description": weather.weather_description,
            "wind_speed": weather.wind_speed,
            "wind_speed_unit": weather.wind_speed_unit,
            "precipitation": weather.precipitation,
            "is_day": weather.is_day,
        }

        # Build response data (for caching)
        response_data = {
            "city": coords.city_name,
            "country": coords.country,
            "coordinates": {
                "latitude": coords.latitude,
                "longitude": coords.longitude,
            },
            "current": weather_data,
        }

        # Try to cache the result (errors don't break the request)
        with contextlib.suppress(Exception):
            cache_service.set(cache_key, response_data)

        # Return response
        return jsonify(
            _build_weather_response(
                city=coords.city_name,
                country=coords.country,
                latitude=coords.latitude,
                longitude=coords.longitude,
                weather_data=weather_data,
                cached=False,
                cache_ttl=None,
                request_id=request_id,
            )
        ), 200

    except CityNotFoundError as e:
        return jsonify(
            {
                "error": {
                    "code": "CITY_NOT_FOUND",
                    "message": str(e),
                    "request_id": request_id,
                }
            }
        ), 404

    except GeocodingError as e:
        return jsonify(
            {
                "error": {
                    "code": "GEOCODING_ERROR",
                    "message": f"Failed to geocode city: {e}",
                    "request_id": request_id,
                }
            }
        ), 502

    except WeatherServiceError as e:
        return jsonify(
            {
                "error": {
                    "code": "WEATHER_SERVICE_ERROR",
                    "message": f"Failed to fetch weather data: {e}",
                    "request_id": request_id,
                }
            }
        ), 502

    except Exception:
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            }
        ), 500


def reset_cache_service() -> None:
    """Reset cache service (useful for testing)."""
    global _cache_service
    _cache_service = None
