"""Configuration package providing file loading utilities."""

from .loader import load, ConfigError

__all__ = ["load", "ConfigError"]
