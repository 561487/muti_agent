"""
Structured logging configuration for Contelix.

Replaces ad-hoc ``print()`` calls with structured JSON logging via structlog.
Output is colorized in terminals, JSON when piped (for log aggregation).
"""

import logging
import sys

import structlog

from contelix.config import ENABLE_DEBUG


def configure_logging() -> None:
    """
    Configure structlog for the Contelix application.

    Call once at application startup (e.g., from ``main.py:main()``).

    - Terminal: Colorized, human-readable console output.
    - Piped/redirected: JSON lines for log aggregation (ELK, Loki, etc.).
    - Debug mode: Sets log level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if ENABLE_DEBUG else logging.INFO

    # Determine if we're writing to a terminal
    is_terminal = sys.stderr.isatty()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if is_terminal
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to pass through structlog
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )
