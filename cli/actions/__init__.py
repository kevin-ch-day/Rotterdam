"""Collection of CLI action helpers split across modules."""

from .analysis import analyze_apk_path, analyze_installed_app
from .device import (
    capture_screenshot,
    export_device_report,
    list_installed_packages,
    list_running_processes,
    quick_security_scan,
    scan_dangerous_permissions,
    scan_for_devices,
    show_connected_devices,
    show_detailed_devices,
    show_network_connections,
)
from .health import run_health_check
from .server import launch_web_app, run_server, show_database_status
from .system import run_doctor

__all__ = [
    "run_doctor",
    "show_connected_devices",
    "show_detailed_devices",
    "list_installed_packages",
    "scan_dangerous_permissions",
    "scan_for_devices",
    "list_running_processes",
    "capture_screenshot",
    "show_network_connections",
    "export_device_report",
    "quick_security_scan",
    "analyze_apk_path",
    "analyze_installed_app",
    "launch_web_app",
    "run_server",
    "show_database_status",
    "run_health_check",
]
