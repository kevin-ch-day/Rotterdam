"""Manifest extraction helpers exposed to the CLI."""

from platform.android.analysis.static.extractors.manifest import (
    extract_app_flags,
    extract_components,
    extract_features,
    extract_metadata,
    extract_permission_details,
    extract_permissions,
    extract_sdk_info,
)

__all__ = [
    "extract_permission_details",
    "extract_permissions",
    "extract_components",
    "extract_sdk_info",
    "extract_features",
    "extract_app_flags",
    "extract_metadata",
]

