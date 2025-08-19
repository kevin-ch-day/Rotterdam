"""Simple static analysis utilities for APK files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Sequence

from core import display
from .manifest import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_permissions,
    extract_permission_details,
    extract_sdk_info,
    extract_metadata,
)
from .permissions import categorize_permissions
from .secrets import scan_for_secrets
from .report import calculate_derived_metrics, write_report
from risk_scoring import calculate_risk_score


def _run_tool(cmd: Sequence[str], tool_name: str) -> None:
    """Execute an external tool and surface friendly errors."""
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        display.fail(f"{tool_name} is not installed or not found in PATH")
        raise RuntimeError(f"{tool_name} missing") from None
    except subprocess.CalledProcessError as e:
        display.fail(f"{tool_name} failed: {e}")
        raise RuntimeError(f"{tool_name} execution failed") from e


def analyze_apk(apk_path: str, outdir: str = "analysis") -> Path:
    """Decompile an APK and run simple static analysis.

    Returns the output directory used for analysis.
    """
    apk = Path(apk_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    apktool_dir = out / "apktool"
    jadx_dir = out / "jadx"

    _run_tool(["apktool", "d", str(apk), "-o", str(apktool_dir)], "apktool")

    _run_tool(["jadx", "-d", str(jadx_dir), str(apk)], "jadx")

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
