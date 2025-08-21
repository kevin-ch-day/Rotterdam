"""Configuration helpers for display utilities.

This module re-exports display-related settings from the global
:mod:`app_config` package so modules in :mod:`utils.display_utils` can
access them without importing the full application configuration.
"""

from app_config.app_config import USE_COLOR, ts

__all__ = ["USE_COLOR", "ts"]
