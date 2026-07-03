"""
Structured logging configuration using structlog.

In development: outputs human-readable colored console logs.
In production: outputs JSON-structured logs suitable for log aggregators
(Datadog, CloudWatch, Loki, etc.).

Call configure_logging() once at application startup.
"""

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog for the application.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
                   Sourced from Settings.log_level.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure the standard library logging to feed into structlog.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Suppress overly verbose third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            # Render as a readable console format during development.
            # Replace ConsoleRenderer with JSONRenderer for production.
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
