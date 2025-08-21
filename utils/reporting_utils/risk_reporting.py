"""High level interface for generating and retrieving risk reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from . import report_utils

__all__ = [
    "create_risk_report",
    "get_risk_history",
    "get_latest_report",
    # Backwards compatible aliases
    "report_risk",
    "history",
]


def create_risk_report(
    package_name: str,
    static_metrics: Optional[Dict[str, float]] = None,
    dynamic_metrics: Optional[Dict[str, float]] = None,
    *,
    session: Session | None = None,
) -> Dict[str, Any]:
    """Generate and persist a new risk report."""

    return report_utils.generate_report(
        package_name,
        static_metrics,
        dynamic_metrics,
        session=session,
    )


def get_risk_history(
    package_name: str,
    *,
    session: Session | None = None,
) -> List[Dict[str, Any]]:
    """Return previously generated risk reports for ``package_name``."""

    return report_utils.fetch_history(package_name, session=session)


def get_latest_report(
    package_name: str,
    *,
    session: Session | None = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent risk report for ``package_name`` if available."""

    return report_utils.fetch_latest(package_name, session=session)


# Backwards compatible aliases for potential legacy callers
report_risk = create_risk_report
history = get_risk_history
