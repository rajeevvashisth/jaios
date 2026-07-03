import logging
import sys

import structlog

from app.config import get_settings


def configure_logging() -> None:
    """Configure structlog + stdlib logging once, at process startup.

    All agent decisions and tool calls should log through
    ``structlog.get_logger(__name__)`` so log lines are structured JSON in
    non-local environments and readable in local dev — the same call site
    works everywhere.
    """
    settings = get_settings()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    renderer = (
        structlog.dev.ConsoleRenderer()
        if settings.app_env == "local"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
