"""Core application settings loaded from environment variables.

This module uses :class:`pydantic_settings.BaseSettings` to provide a
single source of truth for configuration. Existing modules can
instantiate :func:`get_settings` and access fields instead of reading
`os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from server import serv_config as legacy


class AppSettings(BaseSettings):
    """Runtime configuration for the Rotterdam application."""

    host: str = Field(legacy.DEFAULT_HOST, validation_alias="APP_HOST")
    port: int = Field(legacy.DEFAULT_PORT, validation_alias="APP_PORT")
    log_level: legacy.LogLevel = Field(
        legacy.DEFAULT_LOG_LEVEL, validation_alias="UVICORN_LOG_LEVEL"
    )
    open_browser: bool = Field(True, validation_alias="OPEN_BROWSER")

    model_config = SettingsConfigDict(case_sensitive=False)


@lru_cache
def get_settings() -> AppSettings:
    """Return cached application settings using environment variables."""
    return AppSettings()
