"""Utilities for generating and persisting risk reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from risk_scoring import calculate_risk_score
from sqlalchemy.orm import Session


def generate_report(
    package_name: str,
    static_metrics: Optional[Dict[str, float]] = None,
    dynamic_metrics: Optional[Dict[str, float]] = None,
    *,
    session: Session | None = None,
) -> Dict[str, Any]:
    """Generate a risk report.

    ``session`` is accepted for backwards compatibility but is unused as
    reports are not yet persisted to the database.
    """

    # No database interaction currently required
    _ = session  # Preserve signature for callers expecting it
    result = calculate_risk_score(static_metrics, dynamic_metrics)
    return result


def fetch_history(
    package_name: str,
    *,
    session: Session | None = None,
) -> List[Dict[str, Any]]:
    """Return previously persisted reports for ``package_name``."""

    _ = session  # Placeholder until persistence is implemented
    # Database persistence has not been implemented yet
    return []


def fetch_latest(
    package_name: str,
    *,
    session: Session | None = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent report for ``package_name`` or ``None``."""

    _ = session  # Placeholder until persistence is implemented
    return None
