"""APK analysis helpers."""

from .apk_static import analyze_apk
from .report_utils import write_report
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
    "write_report",
]
