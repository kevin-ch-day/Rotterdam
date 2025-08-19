"""Static APK analysis helpers."""

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
]
