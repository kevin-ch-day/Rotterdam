"""Stub risk reporting helpers."""

from __future__ import annotations
from typing import Any, Dict, List


def create_risk_report(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Create a placeholder risk report."""
    return {}


def get_latest_report(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Return a placeholder latest risk report."""
    return {}


def get_risk_history(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty risk history list."""
    return []


def history(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Alias for ``get_risk_history``."""
    return []


def report_risk(
    app_name: str,
    static: Dict[str, Any] | None = None,
    dynamic: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return a placeholder risk summary with a consistent schema."""
    return {
        "app": app_name,
        "static": static or {},
        "dynamic": dynamic or {},
        "score": 0,
        "breakdown": {},
    }
