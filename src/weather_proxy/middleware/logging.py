"""Structured logging middleware using structlog."""

import logging
import time

import structlog
from flask import Flask, Response, g, request

from weather_proxy.config import get_config
from weather_proxy.middleware.correlation import get_correlation_id


def configure_logging() -> None:
    """Configure structlog for JSON structured logging."""
    config = get_config()

    # Map log level string to logging constant
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_level_map.get(config.log_level.upper(), logging.INFO)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if config.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "weather_proxy") -> structlog.BoundLogger:
    """
    Get a structlog logger with request context.

    Args:
        name: Logger name.

    Returns:
        Configured bound logger.
    """
    logger = structlog.get_logger(name)

    # Add correlation ID if in request context
    try:
        correlation_id = get_correlation_id()
        logger = logger.bind(correlation_id=correlation_id)
    except RuntimeError:
        # Not in request context
        pass

    return logger


def setup_request_logging(app: Flask) -> None:
    """
    Setup request/response logging middleware.

    Args:
        app: Flask application instance.
    """

    @app.before_request
    def log_request_start() -> None:
        """Log incoming request."""
        g.request_start_time = time.time()
        get_correlation_id()  # Ensure correlation ID is set

        logger = get_logger("request")
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            query_string=request.query_string.decode("utf-8"),
            remote_addr=request.remote_addr,
            user_agent=request.user_agent.string,
        )

    @app.after_request
    def log_request_complete(response: Response) -> Response:
        """Log completed request."""
        duration_ms = 0.0
        if hasattr(g, "request_start_time"):
            duration_ms = (time.time() - g.request_start_time) * 1000

        logger = get_logger("request")
        logger.info(
            "request_completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            content_length=response.content_length,
        )

        # Add correlation ID to response headers
        try:
            correlation_id = get_correlation_id()
            response.headers["X-Request-ID"] = correlation_id
        except RuntimeError:
            pass

        return response
