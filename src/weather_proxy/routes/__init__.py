"""API route blueprints."""

from weather_proxy.routes.health import health_bp
from weather_proxy.routes.weather import weather_bp

__all__ = ["health_bp", "weather_bp"]
