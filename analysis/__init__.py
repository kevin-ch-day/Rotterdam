# File: analysis/__init__.py
"""Static APK analysis helpers."""

from __future__ import annotations

from .dependencies import (
    analyze_dependencies,
    find_vulnerable_dependencies,
    load_cve_db,
    parse_apk_dependencies,
)
from .manifest import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_metadata,
    extract_permission_details,
    extract_permissions,
    extract_sdk_info,
)
from .network_security import extract_network_security, parse_network_security_config
from .permissions import categorize_permissions
from .report import calculate_derived_metrics, write_report
from .secrets import scan_for_secrets

# Core imports (required)
from .static import analyze_apk

__all__ = [
    "analyze_apk",
    "extract_permissions",
    "extract_permission_details",
    "extract_components",
    "extract_sdk_info",
    "extract_features",
    "extract_app_flags",
    "extract_metadata",
    "categorize_permissions",
    "scan_for_secrets",
    "parse_apk_dependencies",
    "load_cve_db",
    "find_vulnerable_dependencies",
    "analyze_dependencies",
    "write_report",
    "calculate_derived_metrics",
    "parse_network_security_config",
    "extract_network_security",
]

# Optional: Androguard-based DEX inspection
try:
    from .static_analysis.androguard_utils import (
        summarize_apk,  # type: ignore[import-not-found]
    )
except Exception:
    summarize_apk = None  # type: ignore[assignment]
else:
    __all__.append("summarize_apk")

# Optional: YARA scanning utilities
try:
    from .yara_scan import (  # type: ignore[import-not-found]
        compile_rules,
        scan_directory,
    )
except Exception:
    compile_rules = None  # type: ignore[assignment]
    scan_directory = None  # type: ignore[assignment]
else:
    __all__.extend(["compile_rules", "scan_directory"])

# Optional: APK signature verification
try:
    from .signature import verify_signature  # type: ignore[import-not-found]
except Exception:
    verify_signature = None  # type: ignore[assignment]
else:
    __all__.append("verify_signature")

# Optional: certificate analysis utilities
try:
    from .static_analysis.cert_analysis import (
        analyze_certificates,  # type: ignore[import-not-found]
    )
except Exception:  # pragma: no cover - missing dependencies
    analyze_certificates = None  # type: ignore[assignment]
else:
    __all__.append("analyze_certificates")

# Optional: simple machine learning classifier
try:
    from .machine_learning.ml_model import predict_malicious  # type: ignore[import-not-found]
except Exception:
    predict_malicious = None  # type: ignore[assignment]
else:
    __all__.append("predict_malicious")

# Expose lightweight tool wrappers
try:
    from core.tools import adb, apktool, androguard
except Exception:
    adb = apktool = androguard = None  # type: ignore[assignment]
else:
    __all__.extend(["adb", "apktool", "androguard"])
