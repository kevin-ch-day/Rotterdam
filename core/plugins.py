"""Simple plug-in registry for analyzer extensions."""

from __future__ import annotations

from importlib import metadata
from typing import Any, Callable, Dict

_ANALYZERS: Dict[str, Callable[..., Any]] = {}


def register(name: str, func: Callable[..., Any], *, replace: bool = False) -> None:
    """Register an analyzer ``func`` under ``name``."""
    if not replace and name in _ANALYZERS:
        raise KeyError(f"Analyzer '{name}' already registered")
    _ANALYZERS[name] = func


def analyzer(name: str, *, replace: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator variant of :func:`register`."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        register(name, func, replace=replace)
        return func

    return decorator


def get(name: str) -> Callable[..., Any]:
    """Return the analyzer registered under ``name``."""
    return _ANALYZERS[name]


def available() -> Dict[str, Callable[..., Any]]:
    """Return all registered analyzers."""
    return dict(_ANALYZERS)


def clear() -> None:
    """Remove all registered analyzers (primarily for tests)."""
    _ANALYZERS.clear()


def load_entry_point_plugins(group: str = "rotterdam.analyzers") -> None:
    """Load plug-ins defined as entry points under ``group``."""
    try:
        eps = metadata.entry_points().select(group=group)
    except Exception:  # pragma: no cover - compatibility
        eps = []
    for ep in eps:
        if ep.name not in _ANALYZERS:
            register(ep.name, ep.load())
