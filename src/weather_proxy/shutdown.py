"""Graceful shutdown handling for zero-downtime deployments."""

import signal
import sys
import threading
from typing import Any, Callable

# Flag to indicate shutdown is in progress
_shutdown_event = threading.Event()
_shutdown_callbacks: list[Callable[[], None]] = []


def is_shutting_down() -> bool:
    """Check if the application is shutting down."""
    return _shutdown_event.is_set()


def register_shutdown_callback(callback: Callable[[], None]) -> None:
    """
    Register a callback to be called during shutdown.

    Args:
        callback: Function to call during graceful shutdown.
    """
    _shutdown_callbacks.append(callback)


def _handle_signal(signum: int, frame: Any) -> None:
    """
    Handle shutdown signals (SIGTERM, SIGINT).

    Args:
        signum: Signal number received.
        frame: Current stack frame.
    """
    signal_name = signal.Signals(signum).name
    print(f"\nReceived {signal_name}, initiating graceful shutdown...")

    # Set shutdown flag
    _shutdown_event.set()

    # Execute all registered shutdown callbacks
    for callback in _shutdown_callbacks:
        try:
            callback()
        except Exception as e:
            print(f"Error during shutdown callback: {e}")

    print("Graceful shutdown complete.")
    sys.exit(0)


def setup_signal_handlers() -> None:
    """
    Setup signal handlers for graceful shutdown.

    Handles:
        - SIGTERM: Sent by Kubernetes/Docker for graceful shutdown
        - SIGINT: Sent by Ctrl+C
    """
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)


def cleanup_resources() -> None:
    """Clean up application resources during shutdown."""
    from weather_proxy.routes.weather import reset_cache_service

    print("Cleaning up resources...")

    # Reset cache service (closes Redis connection)
    try:
        reset_cache_service()
        print("  - Cache service closed")
    except Exception as e:
        print(f"  - Error closing cache service: {e}")

    print("Resource cleanup complete.")
