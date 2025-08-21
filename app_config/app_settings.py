"""Core application settings loaded from environment variables.

This module uses :class:`pydantic_settings.BaseSettings` to provide a
single source of truth for configuration. Existing modules can
instantiate :func:`get_settings` and access fields instead of reading
`os.environ` directly.
"""

from __future__ import annotations

import os
import warnings
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from server import serv_config as legacy


def _shim_env(new: str, old: str) -> None:
    if new in os.environ:
        return
    if old in os.environ:
        os.environ[new] = os.environ[old]
        warnings.warn(f"{old} is deprecated; use {new}", DeprecationWarning, stacklevel=2)


_shim_env("ROTTERDAM_APP_HOST", "APP_HOST")
_shim_env("ROTTERDAM_APP_PORT", "APP_PORT")


class AppSettings(BaseSettings):
    """Runtime configuration for the Rotterdam application."""

    host: str = Field(legacy.DEFAULT_HOST, validation_alias="ROTTERDAM_APP_HOST")
    port: int = Field(legacy.DEFAULT_PORT, validation_alias="ROTTERDAM_APP_PORT")
    log_level: legacy.LogLevel = Field(
        legacy.DEFAULT_LOG_LEVEL, validation_alias="UVICORN_LOG_LEVEL"
    )
    open_browser: bool = Field(True, validation_alias="OPEN_BROWSER")

    model_config = SettingsConfigDict(case_sensitive=False)


@lru_cache
def get_settings() -> AppSettings:
    """Return cached application settings using environment variables."""
    return AppSettings()
