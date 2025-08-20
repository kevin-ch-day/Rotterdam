from __future__ import annotations

import csv
import json
import re
from typing import Optional

from core import display, renderers
from devices import discovery, packages, processes, selection
from reports import ieee

from .utils import action_context as _action_context, logger


def show_connected_devices() -> None:
    """List connected devices using basic ``adb devices`` output."""
    with _action_context("show_connected_devices"):
        logger.info("show_connected_devices")
        try:
            output = discovery.check_connected_devices()
            devs = discovery.parse_devices_l(output)
        except RuntimeError as e:
            logger.exception("failed to check connected devices")
            display.fail(str(e))
            return

        display.print_section("ADB Devices")
        if not devs:
            logger.info("no devices attached")
            print("No devices attached.")
            return

        renderers.print_basic_device_table(devs)


def show_detailed_devices() -> None:
    """List devices with manufacturer and OS details."""
    with _action_context("show_detailed_devices"):
        logger.info("show_detailed_devices")
        try:
            detailed = discovery.list_detailed_devices()
        except RuntimeError as e:
            logger.exception("failed to list detailed devices")
            display.fail(str(e))
            return

        if not detailed:
            logger.info("no devices attached")
            display.print_section("Connected Devices (Detailed)")
            print("No devices attached.")
            return

        report = ieee.format_device_inventory(detailed)
        logger.info("found %d devices", len(detailed))
        print(report)


def list_installed_packages(
    serial: str,
    *,
    user: bool = False,
    system: bool = False,
    high_value: bool = False,
    regex: Optional[str] = None,
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    """Display packages installed on the device."""
    with _action_context("list_installed_packages", device_serial=serial):
        logger.info("list_installed_packages")
        try:
            pkg_info = packages.inventory_packages(serial)
        except RuntimeError as e:
            logger.exception("failed to inventory packages")
            display.fail(str(e))
            return

        if user:
            pkg_info = [p for p in pkg_info if not p.get("system")]
        if system:
            pkg_info = [p for p in pkg_info if p.get("system")]
        if high_value:
            pkg_info = [p for p in pkg_info if p.get("high_value")]
        if regex:
            try:
                pattern = re.compile(regex)
                pkg_info = [p for p in pkg_info if pattern.search(p.get("package", ""))]
            except re.error as exc:
                display.fail(f"Invalid regex: {exc}")
                return

        pkg_info.sort(
            key=lambda p: (
                0 if p.get("high_value") else 1,
                0 if not p.get("system") else 1,
                p.get("package", ""),
            )
        )
        if limit is not None:
            pkg_info = pkg_info[:limit]

        display.print_section("Application Inventory")
        if not pkg_info:
            logger.info("no packages found")
            print("No packages found.")
            return

        renderers.print_package_inventory(pkg_info)

        if csv_path:
            try:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "package",
                            "version_name",
                            "installer",
                            "uid",
                            "system",
                            "priv",
                            "high_value",
                        ],
                    )
                    writer.writeheader()
                    writer.writerows(pkg_info)
            except OSError as e:
                display.fail(f"Failed to write CSV: {e}")

        if json_path:
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(pkg_info, f, indent=2)
            except OSError as e:
                display.fail(f"Failed to write JSON: {e}")


def scan_dangerous_permissions(serial: str) -> None:
    """Scan packages for dangerous permissions and display results."""
    with _action_context("scan_dangerous_permissions", device_serial=serial):
        logger.info("scan_dangerous_permissions")
        try:
            risky = packages.scan_for_dangerous_permissions(serial)
        except RuntimeError as e:
            logger.exception("permission scan failed")
            display.fail(str(e))
            return

        display.print_section("Apps with Dangerous Permissions")
        if not risky:
            logger.info("no apps with dangerous permissions")
            print("No apps requesting dangerous permissions found.")
            return
        renderers.print_permission_scan(risky)


def scan_for_devices() -> None:
    """Rescan ADB for devices and display the results."""
    with _action_context("scan_for_devices"):
        logger.info("scan_for_devices")
        try:
            detailed = selection.refresh_devices()
        except RuntimeError as e:
            logger.exception("device scan failed")
            display.fail(str(e))
            return

        display.print_section("Scan Results")
        if not detailed:
            logger.info("no devices discovered")
            print("No devices discovered.")
            return

        renderers.print_basic_device_table(detailed)


def export_device_report(serial: str) -> None:
    """Placeholder for exporting a device report."""
    display.info("Export device report not implemented yet.")


def quick_security_scan(serial: str) -> None:
    """Placeholder for quick security scan."""
    display.info("Quick security scan not implemented yet.")


def list_running_processes(serial: str) -> None:
    """List running processes on the device."""
    with _action_context("list_running_processes", device_serial=serial):
        logger.info("list_running_processes")
        try:
            procs = processes.list_processes(serial)
        except RuntimeError as e:
            logger.exception("process listing failed")
            display.fail(str(e))
            return

        display.print_section("Running Processes")
        if not procs:
            logger.info("no process data available")
            print("No process data available.")
            return
        renderers.print_process_table(procs)

