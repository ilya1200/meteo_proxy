"""Unit tests for GeocodingService."""

import httpx
import pytest
import respx

from weather_proxy.services.geocoding_service import (
    CityNotFoundError,
    Coordinates,
    GeocodingError,
    GeocodingService,
)


@pytest.mark.unit
class TestGeocodingService:
    """Tests for GeocodingService class."""

    @respx.mock
    def test_city_to_coords_success(self) -> None:
        """city_to_coords should return coordinates for valid city."""
        mock_response = {
            "results": [
                {
                    "latitude": 52.52,
                    "longitude": 13.41,
                    "name": "Berlin",
                    "country": "Germany",
                    "country_code": "DE",
                }
            ]
        }

        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = GeocodingService()
        coords = service.city_to_coords("Berlin")

        assert isinstance(coords, Coordinates)
        assert coords.latitude == 52.52
        assert coords.longitude == 13.41
        assert coords.city_name == "Berlin"
        assert coords.country == "Germany"
        assert coords.country_code == "DE"

    @respx.mock
    def test_city_to_coords_not_found(self) -> None:
        """city_to_coords should raise CityNotFoundError for unknown city."""
        mock_response = {"results": []}

        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = GeocodingService()

        with pytest.raises(CityNotFoundError) as exc_info:
            service.city_to_coords("NonExistentCity12345")

        assert "NonExistentCity12345" in str(exc_info.value)

    def test_city_to_coords_empty_name(self) -> None:
        """city_to_coords should raise CityNotFoundError for empty city name."""
        service = GeocodingService()

        with pytest.raises(CityNotFoundError):
            service.city_to_coords("")

        with pytest.raises(CityNotFoundError):
            service.city_to_coords("   ")

    @respx.mock
    def test_city_to_coords_api_error(self) -> None:
        """city_to_coords should raise GeocodingError on API error."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(500)
        )

        service = GeocodingService()

        with pytest.raises(GeocodingError):
            service.city_to_coords("Berlin")

    @respx.mock
    def test_city_to_coords_timeout(self) -> None:
        """city_to_coords should raise GeocodingError on timeout."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        service = GeocodingService()

        with pytest.raises(GeocodingError) as exc_info:
            service.city_to_coords("Berlin")

        assert "timed out" in str(exc_info.value)

    @respx.mock
    def test_city_to_coords_network_error(self) -> None:
        """city_to_coords should raise GeocodingError on network error."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        service = GeocodingService()

        with pytest.raises(GeocodingError):
            service.city_to_coords("Berlin")

    @respx.mock
    def test_validate_city_returns_true_for_valid(self) -> None:
        """validate_city should return True for valid city."""
        mock_response = {
            "results": [
                {
                    "latitude": 52.52,
                    "longitude": 13.41,
                    "name": "Berlin",
                }
            ]
        }

        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = GeocodingService()
        assert service.validate_city("Berlin") is True

    @respx.mock
    def test_validate_city_returns_false_for_invalid(self) -> None:
        """validate_city should return False for invalid city."""
        respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        service = GeocodingService()
        assert service.validate_city("NonExistentCity") is False

    def test_service_uses_custom_base_url(self) -> None:
        """Service should use custom base URL if provided."""
        service = GeocodingService(base_url="https://custom.example.com")
        assert service.base_url == "https://custom.example.com"

    def test_service_uses_custom_timeout(self) -> None:
        """Service should use custom timeout if provided."""
        service = GeocodingService(timeout=30)
        assert service.timeout == 30
