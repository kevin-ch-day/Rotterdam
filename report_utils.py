"""Utilities for generating and persisting risk reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from risk_scoring import calculate_risk_score
from storage.repository import RiskReportRepository


def generate_report(
    package_name: str,
    static_metrics: Optional[Dict[str, float]] = None,
    dynamic_metrics: Optional[Dict[str, float]] = None,
    *,
    repository: Optional[RiskReportRepository] = None,
) -> Dict[str, Any]:
    """Generate a risk report and persist it via ``repository``.

    Parameters
    ----------
    package_name:
        Identifier of the application being analysed.
    static_metrics, dynamic_metrics:
        Metric dictionaries forwarded to :func:`calculate_risk_score`.
    repository:
        Optional :class:`RiskReportRepository` instance.  A default in-memory
        repository will be created if omitted.
    """

    repo = repository or RiskReportRepository()
    result = calculate_risk_score(static_metrics, dynamic_metrics)
    repo.add_report(package_name, result["score"], result["rationale"], result["breakdown"])
    return result


def fetch_history(
    package_name: str,
    *,
    repository: Optional[RiskReportRepository] = None,
) -> List[Dict[str, Any]]:
    """Return previously persisted reports for ``package_name``."""

    repo = repository or RiskReportRepository()
    reports = repo.list_reports(package_name)
    return [r.to_dict() for r in reports]


def fetch_latest(
    package_name: str,
    *,
    repository: Optional[RiskReportRepository] = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent report for ``package_name`` or ``None``."""

    repo = repository or RiskReportRepository()
    report = repo.get_latest(package_name)
    return report.to_dict() if report else None
