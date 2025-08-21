"""Application configuration powered by pydantic-settings.

This package centralizes environment-driven settings and path
configuration so modules across the project can share defaults and
behaviour.
"""

from .app import AppSettings, get_settings

__all__ = ["AppSettings", "get_settings"]
