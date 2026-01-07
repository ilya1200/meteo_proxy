"""Unit tests for WeatherService."""

import httpx
import pytest
import respx

from weather_proxy.services.weather_service import (
    WeatherData,
    WeatherService,
    WeatherServiceError,
)


@pytest.mark.unit
class TestWeatherService:
    """Tests for WeatherService class."""

    @respx.mock
    def test_get_weather_success(self) -> None:
        """get_weather should return weather data for valid coordinates."""
        mock_response = {
            "current": {
                "temperature_2m": 15.5,
                "relative_humidity_2m": 65,
                "apparent_temperature": 14.2,
                "weather_code": 3,
                "wind_speed_10m": 12.5,
                "precipitation": 0,
                "is_day": 1,
            },
            "current_units": {
                "temperature_2m": "°C",
                "wind_speed_10m": "km/h",
            },
        }

        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = WeatherService()
        weather = service.get_weather(52.52, 13.41)

        assert isinstance(weather, WeatherData)
        assert weather.temperature == 15.5
        assert weather.temperature_unit == "°C"
        assert weather.humidity == 65
        assert weather.apparent_temperature == 14.2
        assert weather.weather_code == 3
        assert weather.weather_description == "Overcast"
        assert weather.wind_speed == 12.5
        assert weather.wind_speed_unit == "km/h"
        assert weather.precipitation == 0
        assert weather.is_day is True

    @respx.mock
    def test_get_weather_api_error(self) -> None:
        """get_weather should raise WeatherServiceError on API error."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(500)
        )

        service = WeatherService()

        with pytest.raises(WeatherServiceError):
            service.get_weather(52.52, 13.41)

    @respx.mock
    def test_get_weather_timeout(self) -> None:
        """get_weather should raise WeatherServiceError on timeout."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        service = WeatherService()

        with pytest.raises(WeatherServiceError) as exc_info:
            service.get_weather(52.52, 13.41)

        assert "timed out" in str(exc_info.value)

    @respx.mock
    def test_get_weather_network_error(self) -> None:
        """get_weather should raise WeatherServiceError on network error."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        service = WeatherService()

        with pytest.raises(WeatherServiceError):
            service.get_weather(52.52, 13.41)

    @respx.mock
    def test_get_weather_invalid_response(self) -> None:
        """get_weather should raise WeatherServiceError on invalid response."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json={"invalid": "response"})
        )

        service = WeatherService()

        with pytest.raises(WeatherServiceError) as exc_info:
            service.get_weather(52.52, 13.41)

        assert "Invalid response" in str(exc_info.value)

    @respx.mock
    def test_get_weather_handles_night_time(self) -> None:
        """get_weather should correctly handle night time (is_day=0)."""
        mock_response = {
            "current": {
                "temperature_2m": 10.0,
                "weather_code": 0,
                "wind_speed_10m": 5.0,
                "is_day": 0,
            },
            "current_units": {
                "temperature_2m": "°C",
                "wind_speed_10m": "km/h",
            },
        }

        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = WeatherService()
        weather = service.get_weather(52.52, 13.41)

        assert weather.is_day is False

    @respx.mock
    def test_get_weather_unknown_weather_code(self) -> None:
        """get_weather should handle unknown weather codes."""
        mock_response = {
            "current": {
                "temperature_2m": 10.0,
                "weather_code": 999,
                "wind_speed_10m": 5.0,
            },
            "current_units": {},
        }

        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = WeatherService()
        weather = service.get_weather(52.52, 13.41)

        assert weather.weather_description == "Unknown"

    @respx.mock
    def test_is_available_returns_true(self) -> None:
        """is_available should return True when API is reachable."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(200, json={})
        )

        service = WeatherService()
        assert service.is_available() is True

    @respx.mock
    def test_is_available_returns_false_on_error(self) -> None:
        """is_available should return False when API is unreachable."""
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        service = WeatherService()
        assert service.is_available() is False

    def test_service_uses_custom_base_url(self) -> None:
        """Service should use custom base URL if provided."""
        service = WeatherService(base_url="https://custom.example.com")
        assert service.base_url == "https://custom.example.com"

    def test_service_uses_custom_timeout(self) -> None:
        """Service should use custom timeout if provided."""
        service = WeatherService(timeout=30)
        assert service.timeout == 30
