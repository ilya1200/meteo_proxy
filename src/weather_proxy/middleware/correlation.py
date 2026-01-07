"""Correlation ID middleware for request tracing."""

import uuid

from flask import g, request


def get_correlation_id() -> str:
    """
    Get or generate correlation ID for the current request.

    Checks for existing correlation ID in:
    1. Flask g object (already generated)
    2. X-Request-ID header (from upstream)
    3. X-Correlation-ID header (from upstream)

    Returns:
        Correlation ID string.
    """
    # Check if already set in g
    if hasattr(g, "correlation_id") and g.correlation_id:
        return g.correlation_id

    # Check headers
    correlation_id = (
        request.headers.get("X-Request-ID")
        or request.headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )

    # Store in g for reuse
    g.correlation_id = correlation_id
    return correlation_id


def set_correlation_id(correlation_id: str | None = None) -> str:
    """
    Set correlation ID for the current request context.

    Args:
        correlation_id: Optional ID to set. Generates new UUID if not provided.

    Returns:
        The correlation ID that was set.
    """
    g.correlation_id = correlation_id or str(uuid.uuid4())
    return g.correlation_id
