"""Unified reporting utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from risk_scoring import calculate_risk_score
from sqlalchemy.orm import Session

__all__ = [
    "generate",
    "history",
    "latest",
    # Backwards-compatible aliases
    "create_risk_report",
    "report_risk",
    "get_risk_history",
    "get_latest_report",
]


def generate(
    package_name: str,
    static_metrics: Optional[Dict[str, float]] = None,
    dynamic_metrics: Optional[Dict[str, float]] = None,
    *,
    session: Session | None = None,
) -> Dict[str, Any]:
    """Generate a risk report.

    ``session`` is accepted for future compatibility but is currently unused as
    reports are not persisted.
    """

    _ = session  # placeholder until persistence is implemented
    return calculate_risk_score(static_metrics, dynamic_metrics)


def history(
    package_name: str,
    *,
    session: Session | None = None,
) -> List[Dict[str, Any]]:
    """Return previously persisted reports for ``package_name``."""

    _ = session  # placeholder until persistence is implemented
    return []


def latest(
    package_name: str,
    *,
    session: Session | None = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent report for ``package_name`` or ``None``."""

    _ = session  # placeholder until persistence is implemented
    return None


# Backwards-compatible aliases
create_risk_report = generate
report_risk = generate
get_risk_history = history
get_latest_report = latest
