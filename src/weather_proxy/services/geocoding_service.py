"""Geocoding service for converting city names to coordinates."""

from dataclasses import dataclass

import httpx
import pybreaker

from weather_proxy.config import get_config
from weather_proxy.resilience.circuit_breaker import (
    CircuitBreakerOpen,
    get_geocoding_breaker,
    with_retry,
)


@dataclass
class Coordinates:
    """Geographic coordinates with city information."""

    latitude: float
    longitude: float
    city_name: str
    country: str | None = None
    country_code: str | None = None


class GeocodingError(Exception):
    """Exception raised when geocoding fails."""

    pass


class CityNotFoundError(GeocodingError):
    """Exception raised when a city cannot be found."""

    pass


class GeocodingService:
    """
    Service for converting city names to geographic coordinates.

    Uses Open-Meteo Geocoding API to resolve city names.
    Includes resilience patterns: retry with backoff and circuit breaker.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Initialize geocoding service.

        Args:
            base_url: Open-Meteo geocoding API base URL. Defaults to config.
            timeout: Request timeout in seconds. Defaults to config.
        """
        config = get_config()
        self.base_url = base_url or config.open_meteo_geocoding_url
        self.timeout = timeout or config.request_timeout_seconds

    def city_to_coords(self, city_name: str) -> Coordinates:
        """
        Convert a city name to geographic coordinates.

        Uses retry logic and circuit breaker for resilience.

        Args:
            city_name: Name of the city to look up.

        Returns:
            Coordinates object with latitude, longitude, and city info.

        Raises:
            CityNotFoundError: If the city cannot be found.
            GeocodingError: If the API request fails.
        """
        if not city_name or not city_name.strip():
            raise CityNotFoundError("City name cannot be empty")

        city_name = city_name.strip()

        try:
            data = self._fetch_geocoding_data(city_name)
        except CircuitBreakerOpen as e:
            raise GeocodingError(
                "Geocoding service temporarily unavailable (circuit breaker open)"
            ) from e

        if "results" not in data or len(data["results"]) == 0:
            raise CityNotFoundError(f"Could not find city: {city_name}")

        result = data["results"][0]

        return Coordinates(
            latitude=result["latitude"],
            longitude=result["longitude"],
            city_name=result.get("name", city_name),
            country=result.get("country"),
            country_code=result.get("country_code"),
        )

    @with_retry()
    def _fetch_geocoding_data(self, city_name: str) -> dict:
        """
        Fetch geocoding data from API with retry logic.

        Args:
            city_name: Name of the city to look up.

        Returns:
            API response data.

        Raises:
            GeocodingError: If the API request fails after retries.
        """
        breaker = get_geocoding_breaker()

        try:
            return breaker.call(self._make_request, city_name)
        except pybreaker.CircuitBreakerError as e:
            raise CircuitBreakerOpen("Geocoding service circuit breaker is open") from e
        except httpx.TimeoutException as e:
            raise GeocodingError(f"Geocoding request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise GeocodingError(
                f"Geocoding API error: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise GeocodingError(f"Geocoding request failed: {e}") from e

    def _make_request(self, city_name: str) -> dict:
        """Make the actual HTTP request."""
        response = httpx.get(
            f"{self.base_url}/v1/search",
            params={
                "name": city_name,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def validate_city(self, city_name: str) -> bool:
        """
        Validate that a city name can be resolved.

        Args:
            city_name: Name of the city to validate.

        Returns:
            True if the city can be resolved, False otherwise.
        """
        try:
            self.city_to_coords(city_name)
            return True
        except GeocodingError:
            return False
