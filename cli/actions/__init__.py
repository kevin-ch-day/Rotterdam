"""Collection of CLI action helpers split across modules."""

from __future__ import annotations

# Analysis helpers (with optional extras)
from .analysis import analyze_apk_path, analyze_installed_app
try:
    # Optional helpers that may not exist on all branches
    from .analysis import explore_installed_app, sandbox_analyze_apk  # type: ignore
except Exception:
    explore_installed_app = None  # type: ignore[assignment]
    sandbox_analyze_apk = None  # type: ignore[assignment]

from .device import (
    export_device_report,
    list_installed_packages,
    list_running_processes,
    quick_security_scan,
    scan_dangerous_permissions,
    scan_for_devices,
    show_connected_devices,
    show_detailed_devices,
)
from .server import launch_web_app, run_server, show_database_status
from .system import run_doctor, run_health_check

__all__ = [
    "run_doctor",
    "run_health_check",
    "show_connected_devices",
    "show_detailed_devices",
    "list_installed_packages",
    "scan_dangerous_permissions",
    "scan_for_devices",
    "list_running_processes",
    "export_device_report",
    "quick_security_scan",
    "analyze_apk_path",
    "analyze_installed_app",
    "launch_web_app",
    "run_server",
    "show_database_status",
]

# Only export optional helpers if they exist
if explore_installed_app:
    __all__.append("explore_installed_app")
if sandbox_analyze_apk:
    __all__.append("sandbox_analyze_apk")