# File: analysis/__init__.py
"""Static APK analysis helpers."""

from __future__ import annotations

# Core imports (required)
from .static_analysis.static import analyze_apk
from .static_analysis.manifest import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_permissions,
    extract_permission_details,
    extract_sdk_info,
    extract_metadata,
)
from .static_analysis.permissions import categorize_permissions
from .static_analysis.network_security import (
    parse_network_security_config,
    extract_network_security,
)

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
    "parse_network_security_config",
    "extract_network_security",
]

# Optional: Androguard-based DEX inspection
try:
    from .static_analysis.androguard_utils import summarize_apk  # type: ignore[import-not-found]
except Exception:
    summarize_apk = None  # type: ignore[assignment]
else:
    __all__.append("summarize_apk")

# Optional components (to be reintroduced later)
# from .secrets import scan_for_secrets
# from .yara_scan import compile_rules, scan_directory
# from .signature import verify_signature
# from .machine_learning.ml_model import predict_malicious

# Optional: certificate analysis utilities
try:
    from .static_analysis.cert_analysis import analyze_certificates  # type: ignore[import-not-found]

except Exception:  # pragma: no cover - missing dependencies
    analyze_certificates = None  # type: ignore[assignment]
else:
    __all__.append("analyze_certificates")

# Expose lightweight tool wrappers
from core.tools import adb, apktool, androguard
__all__.extend(["adb", "apktool", "androguard"])
