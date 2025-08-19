"""Simple static analysis utilities for APK files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

from .manifest_utils import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_permissions,
    extract_permission_details,
    extract_sdk_info,
    extract_metadata,
)
from .permission_utils import categorize_permissions
from .secret_utils import scan_for_secrets
from .report_utils import calculate_derived_metrics, write_report
from analysis_scoring import calculate_risk_score


def analyze_apk(apk_path: str, outdir: str = "analysis") -> Path:
    """Decompile an APK and run simple static analysis.

    Returns the output directory used for analysis.
    """
    apk = Path(apk_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    apktool_dir = out / "apktool"
    jadx_dir = out / "jadx"

    subprocess.run([
        "apktool",
        "d",
        str(apk),
        "-o",
        str(apktool_dir),
    ], check=True, stdout=subprocess.DEVNULL)

    subprocess.run([
        "jadx",
        "-d",
        str(jadx_dir),
        str(apk),
    ], check=True, stdout=subprocess.DEVNULL)

    manifest = apktool_dir / "AndroidManifest.xml"
    perms: List[str] = []
    perm_uses: List[Dict[str, Any]] = []
    perm_details: List[Dict[str, Any]] = []
    components: Dict[str, List[Dict[str, Any]]] = {}
    sdk_info: Dict[str, int] = {}
    features: List[Dict[str, Any]] = []
    app_flags: Dict[str, bool] = {}
    metadata: List[Dict[str, str]] = []
    if manifest.exists():
        manifest_text = manifest.read_text()
        perm_uses = extract_permission_details(manifest_text)
        perms = extract_permissions(manifest_text)
        (out / "permissions.txt").write_text("\n".join(perms))
        perm_details = categorize_permissions(perm_uses)
        (out / "permission_details.json").write_text(json.dumps(perm_details, indent=2))
        components = extract_components(manifest_text)
        (out / "components.json").write_text(json.dumps(components, indent=2))
        sdk_info = extract_sdk_info(manifest_text)
        (out / "sdk_info.json").write_text(json.dumps(sdk_info, indent=2))
        features = extract_features(manifest_text)
        (out / "features.json").write_text(json.dumps(features, indent=2))
        app_flags = extract_app_flags(manifest_text)
        (out / "app_flags.json").write_text(json.dumps(app_flags, indent=2))
        metadata = extract_metadata(manifest_text)
        (out / "metadata.json").write_text(json.dumps(metadata, indent=2))

    secrets = scan_for_secrets(jadx_dir)
    if secrets:
        (out / "secrets.txt").write_text("\n".join(secrets))

    metrics = calculate_derived_metrics(
        perm_details, components, sdk_info, features, metadata
    )
    (out / "derived_metrics.json").write_text(json.dumps(metrics, indent=2))

    # Placeholder for dynamic metrics; future instrumentation can populate these
    dynamic_metrics: Dict[str, float] = {}
    risk = calculate_risk_score(metrics, dynamic_metrics)
    (out / "risk_score.json").write_text(json.dumps(risk, indent=2))

    write_report(
        out,
        perms,
        perm_details,
        secrets,
        components,
        sdk_info,
        features,
        app_flags,
        metadata,
        metrics,
        risk,
    )

    return out


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m apk_analysis.apk_static <apk> [output_dir]")
        raise SystemExit(1)

    apk_file = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else "analysis"
    analyze_apk(apk_file, dest)
