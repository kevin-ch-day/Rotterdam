"""Reporting helpers for APK static analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


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
            },
            indent=2,
        )
    )
    return report_path
