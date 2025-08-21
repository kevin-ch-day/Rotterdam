from __future__ import annotations

import logging
from contextlib import contextmanager

from .logging_config import StructuredLogger


class AppLogger:
    """Singleton facade for :class:`StructuredLogger`.

    Provides an object-oriented API that can be imported throughout the
    application to retrieve loggers and manage contextual fields.
    """

    _instance: "AppLogger | None" = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Return a logger configured for structured output."""
        return StructuredLogger.get_logger(name)

    def set_session_id(self, session_id: str) -> None:
        """Bind a session identifier to all subsequent log records."""
        StructuredLogger.set_session_id(session_id)

    @contextmanager
    def context(
        self,
        *,
        device_serial: str | None = None,
        action: str | None = None,
        apk_path: str | None = None,
    ):
        """Inject contextual fields into log records within the ``with`` block."""
        with StructuredLogger.context(
            device_serial=device_serial, action=action, apk_path=apk_path
        ):
            yield


# Shared singleton instance for convenience
app_logger = AppLogger()
