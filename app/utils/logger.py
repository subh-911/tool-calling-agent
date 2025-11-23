"""
Structured logging configuration using structlog.
"""

import logging
import sys
from typing import Any
import structlog
from structlog.types import FilteringBoundLogger

from app.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up:
    - JSON output in production
    - Pretty console output in development
    - Correlation IDs for request tracking
    - Automatic exception logging
    """
    # Determine output format based on environment
    if settings.environment == "production":
        # JSON output for production (machine-readable)
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty console output for development (human-readable)
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use our format
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(settings.log_level),
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_request", user_id=123, action="create")
    """
    return structlog.get_logger(name)


# Convenience function for adding correlation IDs
def bind_correlation_id(correlation_id: str) -> None:
    """
    Bind a correlation ID to the current context.

    This ID will be included in all subsequent log messages
    within the current execution context.

    Args:
        correlation_id: Unique identifier for the request/operation
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def unbind_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    structlog.contextvars.unbind_contextvars("correlation_id")
