"""Integration tests for /weather endpoint."""

import httpx
import pytest
import respx
from flask.testing import FlaskClient


@pytest.mark.integration
class TestWeatherEndpoint:
    """Tests for the weather endpoint."""

    def test_weather_missing_city_parameter(self, client: FlaskClient) -> None:
        """Weather endpoint should return 400 for missing city parameter."""
        response = client.get("/weather")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"
        assert "request_id" in data["error"]

    def test_weather_empty_city_parameter(self, client: FlaskClient) -> None:
        """Weather endpoint should return 400 for empty city parameter."""
        response = client.get("/weather?city=")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_weather_whitespace_city_parameter(self, client: FlaskClient) -> None:
        """Weather endpoint should return 400 for whitespace-only city."""
        response = client.get("/weather?city=   ")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_weather_city_too_long(self, client: FlaskClient) -> None:
        """Weather endpoint should return 400 for city name > 100 chars."""
        long_city = "a" * 101
        response = client.get(f"/weather?city={long_city}")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_PARAMETER"

    @respx.mock
    def test_weather_city_not_found(self, client: FlaskClient) -> None:
        """Weather endpoint should return 404 for unknown city."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        response = client.get("/weather?city=NonExistentCity12345")
        assert response.status_code == 404
        data = response.get_json()
        assert data["error"]["code"] == "CITY_NOT_FOUND"

    @respx.mock
    def test_weather_success(self, client: FlaskClient) -> None:
        """Weather endpoint should return 200 with valid city."""
        # Mock geocoding response
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "latitude": 52.52,
                            "longitude": 13.41,
                            "name": "Berlin",
                            "country": "Germany",
                            "country_code": "DE",
                        }
                    ]
                },
            )
        )

        # Mock weather response
        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(
                200,
                json={
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
                },
            )
        )

        response = client.get("/weather?city=Berlin")
        assert response.status_code == 200

        data = response.get_json()
        assert data["city"] == "Berlin"
        assert data["country"] == "Germany"
        assert data["coordinates"]["latitude"] == 52.52
        assert data["coordinates"]["longitude"] == 13.41
        assert data["current"]["temperature"] == 15.5
        assert data["current"]["weather_code"] == 3
        assert data["current"]["weather_description"] == "Overcast"
        assert "request_id" in data

    @respx.mock
    def test_weather_response_structure(self, client: FlaskClient) -> None:
        """Weather response should have expected structure."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "latitude": 48.85,
                            "longitude": 2.35,
                            "name": "Paris",
                            "country": "France",
                        }
                    ]
                },
            )
        )

        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(
                200,
                json={
                    "current": {
                        "temperature_2m": 20.0,
                        "weather_code": 1,
                        "wind_speed_10m": 10.0,
                    },
                    "current_units": {},
                },
            )
        )

        response = client.get("/weather?city=Paris")
        data = response.get_json()

        # Check required top-level fields
        assert "city" in data
        assert "coordinates" in data
        assert "current" in data
        assert "cached" in data
        assert "request_id" in data

        # Check coordinates structure
        assert "latitude" in data["coordinates"]
        assert "longitude" in data["coordinates"]

        # Check current weather structure
        assert "temperature" in data["current"]
        assert "temperature_unit" in data["current"]
        assert "weather_code" in data["current"]
        assert "weather_description" in data["current"]
        assert "wind_speed" in data["current"]
        assert "wind_speed_unit" in data["current"]

    @respx.mock
    def test_weather_geocoding_error(self, client: FlaskClient) -> None:
        """Weather endpoint should return 502 on geocoding API error."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(500)
        )

        response = client.get("/weather?city=Berlin")
        assert response.status_code == 502
        data = response.get_json()
        assert data["error"]["code"] == "GEOCODING_ERROR"

    @respx.mock
    def test_weather_api_error(self, client: FlaskClient) -> None:
        """Weather endpoint should return 502 on weather API error."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "latitude": 52.52,
                            "longitude": 13.41,
                            "name": "Berlin",
                        }
                    ]
                },
            )
        )

        respx.get("https://api.open-meteo.com/v1/forecast").mock(
            return_value=httpx.Response(500)
        )

        response = client.get("/weather?city=Berlin")
        assert response.status_code == 502
        data = response.get_json()
        assert data["error"]["code"] == "WEATHER_SERVICE_ERROR"

    def test_weather_returns_json(self, client: FlaskClient) -> None:
        """Weather endpoint should always return JSON."""
        response = client.get("/weather")
        assert response.content_type == "application/json"
