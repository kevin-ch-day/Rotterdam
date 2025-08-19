"""Static APK analysis helpers."""

from __future__ import annotations

# Core imports (required)
from .static import analyze_apk
from .report import calculate_derived_metrics, write_report
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
from .dependencies import (
    parse_apk_dependencies,
    load_cve_db,
    find_vulnerable_dependencies,
    analyze_dependencies,
)
from .network_security import parse_network_security_config, extract_network_security

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

# Optional: YARA scanning utilities
try:
    from .yara_scan import compile_rules, scan_directory  # type: ignore[import-not-found]

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
