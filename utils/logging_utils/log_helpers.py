from __future__ import annotations

"""Helper utilities built on top of :mod:`app_logger`.

These helpers provide a lightweight, function-based interface for the
application to emit log messages without needing to interact with the
underlying logger objects directly.
"""

from .app_logger import app_logger


class LoggingHelper:
    """Convenience helpers for emitting log messages through ``app_logger``."""

    @staticmethod
    def info(message: str, *, logger_name: str | None = None) -> None:
        """Log an informational message."""
        app_logger.get_logger(logger_name).info(message)

    @staticmethod
    def warning(message: str, *, logger_name: str | None = None) -> None:
        """Log a warning message."""
        app_logger.get_logger(logger_name).warning(message)

    @staticmethod
    def error(
        message: str,
        *,
        logger_name: str | None = None,
        exc: Exception | None = None,
    ) -> None:
        """Log an error message and optional exception information."""
        app_logger.get_logger(logger_name).error(message, exc_info=exc)
