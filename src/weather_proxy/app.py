"""Flask application factory."""

import time

from flask import Flask, g

from weather_proxy import __version__
from weather_proxy.config import get_config

# Application start time for uptime calculation
_start_time: float = time.time()


def get_uptime_seconds() -> float:
    """Get application uptime in seconds."""
    return time.time() - _start_time


def create_app(
    config_override: dict | None = None, setup_signals: bool = True
) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_override: Optional dictionary of configuration overrides for testing.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    app_config = get_config()
    app.config["DEBUG"] = app_config.debug
    app.config["SECRET_KEY"] = app_config.secret_key

    # Store config in app for access in routes
    app.config["APP_CONFIG"] = app_config
    app.config["APP_VERSION"] = __version__

    # Apply any configuration overrides (useful for testing)
    if config_override:
        app.config.update(config_override)

    # Configure structured logging
    from weather_proxy.middleware.logging import (
        configure_logging,
        setup_request_logging,
    )

    configure_logging()

    # Initialize metrics
    from weather_proxy.utils.metrics import init_metrics

    init_metrics(__version__)

    # Setup request/response logging (unless testing)
    if not app.config.get("TESTING"):
        setup_request_logging(app)

    # Setup graceful shutdown handlers (unless testing)
    if setup_signals and not app.config.get("TESTING"):
        from weather_proxy.shutdown import (
            cleanup_resources,
            register_shutdown_callback,
            setup_signal_handlers,
        )

        setup_signal_handlers()
        register_shutdown_callback(cleanup_resources)

    # Register before_request handler to track request timing
    @app.before_request
    def before_request() -> None:
        g.request_start_time = time.time()

    # Register blueprints
    _register_blueprints(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from weather_proxy.routes.health import health_bp
    from weather_proxy.routes.weather import weather_bp
    from weather_proxy.utils.metrics import metrics_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(metrics_bp)
