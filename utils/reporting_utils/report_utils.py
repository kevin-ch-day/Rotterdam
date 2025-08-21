"""Placeholder report utilities."""
from __future__ import annotations

def fetch_history(*args, **kwargs):
    """Return an empty history list."""
    return []

def fetch_latest(*args, **kwargs):
    """Return ``None`` to indicate no latest report."""
    return None

def generate_report(*args, **kwargs):
    """Return a placeholder risk report structure.

    The full reporting subsystem has been stripped for the MVP, but callers
    in the static analysis pipeline still expect a mapping of risk metrics.
    Returning an empty ``dict`` keeps the interface intact without performing
    any scoring logic.
    """

    return {}
