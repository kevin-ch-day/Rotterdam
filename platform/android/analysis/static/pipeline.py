"""Simple static analysis utilities for APK files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app_config import app_config
from utils.display_utils import display

from .adapters import apktool, jadx
from .diff import diff_snapshots
from .extractors.manifest import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_metadata,
    extract_permission_details,
    extract_permissions,
    extract_sdk_info,
)
from .extractors.network import extract_network_security
from .extractors.permissions import categorize_permissions
from .extractors.secrets import scan_for_secrets
from .ml_model import predict_malicious
from .report.writer import calculate_derived_metrics, write_report
from .rules.engine import evaluate_rules, load_rules

# Optional imports (degrade gracefully if unavailable)
try:
    from .yara_scan import scan_directory  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    scan_directory = None  # type: ignore[assignment]

try:
    from .extractors.signing import verify_signature  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    verify_signature = None  # type: ignore[assignment]

try:
    from .adapters.androguard import summarize_apk  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    summarize_apk = None  # type: ignore[assignment]

try:
    from .extractors.crypto import (
        analyze_certificates,  # type: ignore[import-not-found]
    )
except Exception:  # pragma: no cover
    analyze_certificates = None  # type: ignore[assignment]

# Risk scoring
import reporting


def analyze_apk(apk_path: str, outdir: str | Path | None = None) -> Path:
    """Decompile an APK and run simple static analysis.

    Returns the output directory used for analysis.
    """
    apk = Path(apk_path)
    out = Path(outdir) if outdir else app_config.OUTPUT_DIR / app_config.ts()
    out.mkdir(parents=True, exist_ok=True)
    apktool_dir = out / "apktool"
    jadx_dir = out / "jadx"

    apktool.decompile(apk, apktool_dir)
    jadx.decompile(apk, jadx_dir)

    manifest = apktool_dir / "AndroidManifest.xml"
    perms: List[str] = []
    perm_uses: List[Dict[str, Any]] = []
    perm_details: List[Dict[str, Any]] = []
    components: Dict[str, List[Dict[str, Any]]] = {}
    sdk_info: Dict[str, int] = {}
    features: List[Dict[str, Any]] = []
    app_flags: Dict[str, bool] = {}
    metadata: List[Dict[str, str]] = []
    network_security: Dict[str, Any] = {}

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

        try:
            network_security = extract_network_security(apktool_dir)
            if network_security:
                (out / "network_security.json").write_text(json.dumps(network_security, indent=2))
        except Exception as e:  # pragma: no cover
            display.warn(f"Network security parsing failed: {e}")
    else:
        display.warn("AndroidManifest.xml not found after apktool decompile")

    # Secrets (from decompiled code/resources)
    secrets = scan_for_secrets(jadx_dir)
    if secrets:
        (out / "secrets.txt").write_text("\n".join(secrets))

    # Optional YARA scan (if available)
    yara_matches: Optional[Dict[str, List[str]]] = None
    if scan_directory:
        try:
            yara_matches = scan_directory(apktool_dir)
            if yara_matches:
                (out / "yara_matches.json").write_text(json.dumps(yara_matches, indent=2))
        except RuntimeError as e:
            display.warn(str(e))
    else:
        display.note("YARA scanning not available (yara_scan module not found)")

    # Optional Androguard analysis for API usage
    androguard_summary: Optional[Dict[str, Any]] = None
    if summarize_apk:
        try:
            androguard_summary = summarize_apk(str(apk))
            (out / "androguard_report.json").write_text(json.dumps(androguard_summary, indent=2))
        except Exception as e:  # pragma: no cover
            display.warn(f"Androguard analysis failed: {e}")
    else:
        display.note("Androguard analysis not available (androguard_utils module not found)")

    # Derived metrics (static)
    metrics = calculate_derived_metrics(perm_details, components, sdk_info, features, metadata)

    # Network security → metrics
    if network_security:
        metrics["cleartext_traffic_permitted"] = (
            1 if network_security.get("cleartext_permitted") else 0
        )
        metrics["missing_certificate_pinning"] = (
            0 if network_security.get("certificate_pinning") else 1
        )
        metrics["debug_overrides"] = 1 if network_security.get("debug_overrides") else 0

    # Enrich metrics with Androguard rule matches if present
    if androguard_summary:
        rule_matches = androguard_summary.get("rule_matches", {})
        for name, matches in rule_matches.items():
            metrics[f"androguard_{name}_count"] = len(matches)

    # Evaluate rules against collected facts
    findings: List[Dict[str, Any]] = []
    try:
        rule_dir = Path(__file__).resolve().parent / "rules" / "packs"
        rules = load_rules(rule_dir)
        facts = {
            "permissions": perms,
            "permission_details": perm_details,
            "components": components,
            "sdk_info": sdk_info,
            "features": features,
            "app_flags": app_flags,
            "metadata": metadata,
            "metrics": metrics,
        }
        findings = evaluate_rules(rules, facts)
        if findings:
            (out / "findings.json").write_text(json.dumps(findings, indent=2))
    except Exception as e:  # pragma: no cover
        display.warn(f"Rule evaluation failed: {e}")

    # Optional signature verification (if available)
    if verify_signature:
        try:
            sig_info = verify_signature(apk_path)
            metrics["untrusted_signature"] = 0 if sig_info.get("trusted") else 1
            (out / "signature.json").write_text(json.dumps(sig_info, indent=2))
        except Exception as e:  # pragma: no cover
            display.warn(f"Signature verification failed: {e}")
    else:
        metrics["untrusted_signature"] = 0  # neutral if we cannot verify
        display.note("Signature verification not available (signature module not found)")

    # Signing certificate analysis (expiry, self-signed, etc.)
    if analyze_certificates:
        try:
            cert_info = analyze_certificates(apk_path)
            metrics["expired_certificate"] = 1 if cert_info.get("expired") else 0
            metrics["self_signed_certificate"] = 1 if cert_info.get("self_signed") else 0
            (out / "cert_info.json").write_text(json.dumps(cert_info, indent=2))
        except Exception as e:  # pragma: no cover
            display.warn(f"Certificate analysis failed: {e}")
    else:
        metrics.setdefault("expired_certificate", 0)
        metrics.setdefault("self_signed_certificate", 0)
        display.note("Certificate analysis not available (cert_analysis module not found)")

    (out / "derived_metrics.json").write_text(json.dumps(metrics, indent=2))

    # Machine learning classification on a subset of normalized metrics
    ml_result: Dict[str, Any] = {"label": "unknown", "confidence": 0.0, "neighbors": []}
    try:
        ml_features = {
            k: metrics[k]
            for k in ("permission_density", "component_exposure", "cleartext_traffic_permitted")
            if k in metrics
        }
        ml_result = predict_malicious(ml_features)
        metrics["ml_pred_malicious"] = 1 if ml_result["label"] == "malicious" else 0
    except Exception as e:  # pragma: no cover - defensive
        metrics["ml_pred_malicious"] = 0
        display.warn(f"ML prediction failed: {e}")
    (out / "ml_prediction.json").write_text(json.dumps(ml_result, indent=2))

    # Placeholder for dynamic metrics; future instrumentation can populate these.
    dynamic_metrics: Dict[str, float] = {}

    # Risk scoring (merges static+dynamic and ML-derived metrics)
    risk = reporting.generate(apk.stem, metrics, dynamic_metrics)
    (out / "risk_score.json").write_text(json.dumps(risk, indent=2))

    # Store a snapshot of key manifest data with a simple version tag
    snapshot = {
        "permissions": perms,
        "components": {k: [c.get("name", "") for c in v] for k, v in components.items()},
    }
    app_config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    base = apk.stem
    existing = sorted(app_config.STORAGE_DIR.glob(f"{base}_v*.json"))
    version = len(existing) + 1
    snap_path = app_config.STORAGE_DIR / f"{base}_v{version}.json"
    snap_path.write_text(json.dumps(snapshot, indent=2))

    diff: Optional[Dict[str, Any]] = None
    if existing:
        prev_path = existing[-1]
        diff = diff_snapshots(prev_path, snap_path)
        (out / "snapshot_diff.json").write_text(json.dumps(diff, indent=2))

    # Final consolidated report (supports both yara_matches and diff)
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
        risk,  # placed into "metrics" bucket as additional fields
        yara_matches,
        diff,
        findings,
    )

    return out
