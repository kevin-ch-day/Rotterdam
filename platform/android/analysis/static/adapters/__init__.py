"""Adapters for external Android analysis tools."""

from . import aapt2, apktool, common, jadx

try:  # pragma: no cover - optional androguard dependency
    from . import androguard  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    androguard = None  # type: ignore[assignment]

__all__ = ["aapt2", "androguard", "apktool", "common", "jadx"]
