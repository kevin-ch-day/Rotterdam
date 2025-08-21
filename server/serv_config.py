# server/serv_config.py
"""
Centralized server configuration shared across the application.
This ensures host/port/logging/etc. stay consistent between
uvicorn serve, API checks, and any error handling code.
"""

from __future__ import annotations

import os
import warnings
from typing import Literal

LogLevel = Literal["critical", "error", "warning", "info", "debug", "trace"]

# Defaults
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765  # safer, less likely to be taken
DEFAULT_LOG_LEVEL: LogLevel = "info"

# Environment overrides


def _env(new: str, old: str, default: str) -> str:
    if (val := os.getenv(new)) is not None:
        return val
    if (val := os.getenv(old)) is not None:
        warnings.warn(f"{old} is deprecated; use {new}", DeprecationWarning, stacklevel=2)
        return val
    return default


HOST: str = _env("ROTTERDAM_APP_HOST", "APP_HOST", DEFAULT_HOST)
try:
    PORT: int = int(_env("ROTTERDAM_APP_PORT", "APP_PORT", str(DEFAULT_PORT)))
except ValueError:
    PORT = DEFAULT_PORT

LOG_LEVEL: LogLevel = os.getenv("UVICORN_LOG_LEVEL", DEFAULT_LOG_LEVEL)  # type: ignore[assignment]
OPEN_BROWSER: bool = os.getenv("OPEN_BROWSER", "true").lower() in {"1", "true", "yes", "on"}

# Helper dict if you want to quickly reuse in uvicorn.Config
CONFIG = {
    "host": HOST,
    "port": PORT,
    "log_level": LOG_LEVEL,
}
