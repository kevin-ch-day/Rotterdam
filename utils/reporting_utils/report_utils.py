"""Stub utilities for report fetching and generation."""

from __future__ import annotations
from typing import Any, Dict, List


def fetch_history(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """Return an empty history list."""
    return []


def fetch_latest(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Return an empty report placeholder (no latest report)."""
    return {}


def generate_report(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Return a dummy report structure."""
    return {}
