"""Reporting helpers for APK static analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def calculate_derived_metrics(
    permission_details: List[Dict[str, Any]],
    components: Dict[str, List[Dict[str, Any]]],
    sdk_info: Dict[str, int] | None = None,
    features: List[Dict[str, Any]] | None = None,
    metadata: List[Dict[str, str]] | None = None,
) -> Dict[str, float]:
    """Compute metrics derived from manifest data.

    In addition to density ratios, this function exposes basic counts
    to help downstream tooling build rich feature vectors.  All inputs
    are optional except ``permission_details`` and ``components``.

    Returned metrics include:

    ``permission_density``
        Ratio of dangerous permissions to total declared permissions.

    ``component_exposure``
        Ratio of exported components to total components.

    ``total_permission_count`` / ``dangerous_permission_count``
        Raw permission counts for feature engineering.

    ``total_component_count`` / ``exported_component_count``
        Raw component counts.

    ``feature_count`` / ``metadata_count``
        Number of ``uses-feature`` and ``meta-data`` entries.

    ``min_sdk`` / ``target_sdk`` / ``max_sdk`` / ``sdk_span``
        SDK version information and span between min and target.
    """

    features = features or []
    metadata = metadata or []
    sdk_info = sdk_info or {}

    total_perms = len(permission_details)
    dangerous_perms = sum(1 for p in permission_details if p.get("dangerous"))
    perm_density = dangerous_perms / total_perms if total_perms else 0.0

    total_components = sum(len(items) for items in components.values())
    exported_components = sum(
        1 for items in components.values() for item in items if item.get("exported")
    )
    comp_exposure = exported_components / total_components if total_components else 0.0

    min_sdk = sdk_info.get("minSdkVersion", 0)
    target_sdk = sdk_info.get("targetSdkVersion", 0)
    max_sdk = sdk_info.get("maxSdkVersion", 0)
    sdk_span = (target_sdk - min_sdk) if min_sdk and target_sdk else 0

    return {
        "permission_density": round(perm_density, 3),
        "component_exposure": round(comp_exposure, 3),
        "total_permission_count": total_perms,
        "dangerous_permission_count": dangerous_perms,
        "total_component_count": total_components,
        "exported_component_count": exported_components,
        "feature_count": len(features),
        "metadata_count": len(metadata),
        "min_sdk": min_sdk,
        "target_sdk": target_sdk,
        "max_sdk": max_sdk,
        "sdk_span": sdk_span,
    }


def write_report(
    out: Path,
    permissions: List[str],
    permission_details: List[Dict[str, Any]],
    secrets: List[str],
    components: Dict[str, List[Dict[str, Any]]],
    sdk_info: Dict[str, int],
    features: List[Dict[str, Any]],
    app_flags: Dict[str, bool],
    metadata: List[Dict[str, str]],
    metrics: Dict[str, float] | None = None,
) -> Path:
    """Write a JSON report containing analysis results."""
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "permissions": permissions,
                "permission_details": permission_details,
                "secrets": secrets,
                "components": components,
                "sdk_info": sdk_info,
                "features": features,
                "app_flags": app_flags,
                "metadata": metadata,
                "metrics": metrics or {},
            },
            indent=2,
        )
    )
    return report_path
