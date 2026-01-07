"""Configuration management for Weather Proxy Service."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env_file() -> None:
    """Load environment variables from env/.env file."""
    # Look for env/.env relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / "env" / ".env"
    if env_file.exists():
        load_dotenv(env_file)


# Load environment on module import
_load_env_file()


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Flask settings
    flask_env: str = field(default_factory=lambda: os.getenv("FLASK_ENV", "production"))
    debug: bool = field(
        default_factory=lambda: os.getenv("FLASK_ENV", "production") == "development"
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    )

    # Redis settings
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    cache_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300"))
    )

    # Open-Meteo API settings
    open_meteo_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPEN_METEO_BASE_URL", "https://api.open-meteo.com"
        )
    )
    open_meteo_geocoding_url: str = field(
        default_factory=lambda: os.getenv(
            "OPEN_METEO_GEOCODING_URL", "https://geocoding-api.open-meteo.com"
        )
    )

    # Resilience settings
    circuit_breaker_fail_max: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", "5"))
    )
    circuit_breaker_reset_timeout: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_RESET_TIMEOUT", "60"))
    )
    request_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    )
    retry_max_attempts: int = field(
        default_factory=lambda: int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    )

    # Logging settings
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "json"))

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()


# Global configuration instance
config = Config.from_env()


def get_config() -> Config:
    """Get the application configuration."""
    return config
