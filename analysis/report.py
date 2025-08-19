"""Reporting helpers for APK static analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from collections import Counter


def _permission_prefix_counts(permission_details: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return counts of permission name prefixes.

    The prefix is taken from the last segment of the permission name up to the
    first underscore. For example, ``android.permission.READ_CONTACTS`` maps to
    the ``READ`` prefix. These counts help highlight broad capability patterns
    requested by an application.
    """
    prefixes: List[str] = []
    for p in permission_details:
        name = p.get("name", "")
        tail = name.rsplit(".", 1)[-1]
        prefix = tail.split("_", 1)[0]
        if prefix:
            prefixes.append(prefix)
    return dict(Counter(prefixes))


def calculate_derived_metrics(
    permission_details: List[Dict[str, Any]],
    components: Dict[str, List[Dict[str, Any]]],
    sdk_info: Dict[str, int] | None = None,
    features: List[Dict[str, Any]] | None = None,
    metadata: List[Dict[str, str]] | None = None,
    dynamic_metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compute metrics derived from manifest data.

    In addition to density ratios, this function exposes basic counts
    to help downstream tooling build rich feature vectors. All inputs
    are optional except ``permission_details`` and ``components``.

    Returned metrics include:

    ``permission_density``            Ratio of dangerous to total permissions.
    ``component_exposure``            Ratio of exported to total components.
    ``total_permission_count``        Raw permission count.
    ``dangerous_permission_count``    Raw dangerous permission count.
    ``total_component_count``         Raw component count.
    ``exported_component_count``      Raw exported component count.
    ``feature_count`` / ``metadata_count``  uses-feature/meta-data counts.
    ``min_sdk`` / ``target_sdk`` / ``max_sdk`` / ``sdk_span``  SDK info.
    """
    features = features or []
    metadata = metadata or []
    sdk_info = sdk_info or {}
    dynamic_metrics = dynamic_metrics or {}

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

    metrics: Dict[str, Any] = {
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

    prefix_counts = _permission_prefix_counts(permission_details)
    if prefix_counts:
        metrics["permission_prefix_counts"] = prefix_counts

    # Merge provided dynamic metrics (runtime observations).
    metrics.update(dynamic_metrics)

    # Combined metrics tying runtime behavior to static declarations.
    perm_usage = dynamic_metrics.get("permission_usage_counts")
    runtime_perm_count = dynamic_metrics.get("unique_permission_count")
    if perm_usage and runtime_perm_count is None:
        runtime_perm_count = len(perm_usage)

    if runtime_perm_count is not None:
        metrics["runtime_permission_count"] = runtime_perm_count
        metrics["unused_permission_count"] = max(total_perms - runtime_perm_count, 0)
        coverage = runtime_perm_count / total_perms if total_perms else 0.0
        metrics["runtime_permission_coverage"] = round(coverage, 3)

    if "network_endpoints" in dynamic_metrics and "network_endpoint_count" not in metrics:
        metrics["network_endpoint_count"] = len(dynamic_metrics["network_endpoints"])

    # Prefer new name; add legacy alias for downstream compatibility.
    if "filesystem_writes" in dynamic_metrics and "filesystem_write_count" not in metrics:
        metrics["filesystem_write_count"] = len(dynamic_metrics["filesystem_writes"])
    if "filesystem_write_count" in metrics and "file_write_count" not in metrics:
        # Back-compat with older consumers expecting file_write_count.
        metrics["file_write_count"] = metrics["filesystem_write_count"]

    return metrics


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
    metrics: Dict[str, Any] | None = None,
    dynamic_metrics: Dict[str, Any] | None = None,
    yara_matches: Dict[str, List[str]] | None = None,
    diff: Dict[str, Any] | None = None,
    findings: List[Dict[str, Any]] | None = None,
) -> Path:
    """Write a JSON report containing analysis results."""
    report_path = out / "report.json"
    all_metrics: Dict[str, Any] = {**(metrics or {}), **(dynamic_metrics or {})}

    data: Dict[str, Any] = {
        "permissions": permissions,
        "permission_details": permission_details,
        "secrets": secrets,
        "components": components,
        "sdk_info": sdk_info,
        "features": features,
        "app_flags": app_flags,
        "metadata": metadata,
        "metrics": all_metrics,
    }
    if yara_matches is not None:
        data["yara_matches"] = yara_matches
    if diff is not None:
        data["diff"] = diff
    if findings is not None:
        data["findings"] = findings

    report_path.write_text(json.dumps(data, indent=2))
    return report_path
