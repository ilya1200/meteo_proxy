"""Weather service for fetching weather data from Open-Meteo API."""

from dataclasses import dataclass

import httpx
import pybreaker

from weather_proxy.config import get_config
from weather_proxy.resilience.circuit_breaker import (
    CircuitBreakerOpen,
    get_weather_breaker,
    with_retry,
)

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass
class WeatherData:
    """Current weather data."""

    temperature: float
    temperature_unit: str
    weather_code: int
    weather_description: str
    wind_speed: float
    wind_speed_unit: str
    humidity: float | None = None
    apparent_temperature: float | None = None
    precipitation: float | None = None
    is_day: bool | None = None


class WeatherServiceError(Exception):
    """Exception raised when weather service fails."""

    pass


class WeatherService:
    """
    Service for fetching weather data from Open-Meteo API.

    Provides current weather conditions for given coordinates.
    Includes resilience patterns: retry with backoff and circuit breaker.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Initialize weather service.

        Args:
            base_url: Open-Meteo API base URL. Defaults to config.
            timeout: Request timeout in seconds. Defaults to config.
        """
        config = get_config()
        self.base_url = base_url or config.open_meteo_base_url
        self.timeout = timeout or config.request_timeout_seconds

    def get_weather(self, latitude: float, longitude: float) -> WeatherData:
        """
        Get current weather for coordinates.

        Uses retry logic and circuit breaker for resilience.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.

        Returns:
            Current weather data.

        Raises:
            WeatherServiceError: If the API request fails.
        """
        try:
            data = self._fetch_weather_data(latitude, longitude)
        except CircuitBreakerOpen as e:
            raise WeatherServiceError(
                "Weather service temporarily unavailable (circuit breaker open)"
            ) from e

        if "current" not in data:
            raise WeatherServiceError("Invalid response from weather API")

        current = data["current"]
        units = data.get("current_units", {})

        weather_code = current.get("weather_code", 0)
        weather_description = WMO_CODES.get(weather_code, "Unknown")

        is_day_value = current.get("is_day")
        is_day = bool(is_day_value) if is_day_value is not None else None

        return WeatherData(
            temperature=current.get("temperature_2m", 0),
            temperature_unit=units.get("temperature_2m", "°C"),
            weather_code=weather_code,
            weather_description=weather_description,
            wind_speed=current.get("wind_speed_10m", 0),
            wind_speed_unit=units.get("wind_speed_10m", "km/h"),
            humidity=current.get("relative_humidity_2m"),
            apparent_temperature=current.get("apparent_temperature"),
            precipitation=current.get("precipitation"),
            is_day=is_day,
        )

    @with_retry()
    def _fetch_weather_data(self, latitude: float, longitude: float) -> dict:
        """
        Fetch weather data from API with retry logic.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.

        Returns:
            API response data.

        Raises:
            WeatherServiceError: If the API request fails after retries.
        """
        breaker = get_weather_breaker()

        try:
            return breaker.call(self._make_request, latitude, longitude)
        except pybreaker.CircuitBreakerError as e:
            raise CircuitBreakerOpen("Weather service circuit breaker is open") from e
        except httpx.TimeoutException as e:
            raise WeatherServiceError(f"Weather request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise WeatherServiceError(
                f"Weather API error: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise WeatherServiceError(f"Weather request failed: {e}") from e

    def _make_request(self, latitude: float, longitude: float) -> dict:
        """Make the actual HTTP request."""
        response = httpx.get(
            f"{self.base_url}/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "weather_code",
                    "wind_speed_10m",
                    "precipitation",
                    "is_day",
                ],
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def is_available(self) -> bool:
        """
        Check if Open-Meteo API is available.

        Returns:
            True if API is reachable, False otherwise.
        """
        try:
            response = httpx.get(
                f"{self.base_url}/v1/forecast",
                params={
                    "latitude": 0,
                    "longitude": 0,
                    "current": "temperature_2m",
                },
                timeout=5,
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False
