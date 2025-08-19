"""High-level device-related actions for the CLI.

These functions wrap lower-level utilities and present formatted
output for the user interface.
"""

from __future__ import annotations

import json
from pathlib import Path

from app_utils import app_display, app_menu_utils, app_renderers
from reporting import ieee_report
from device_analysis import (
    device_discovery,
    package_scanner,
    apk_extractor,
    process_listing,
)
from apk_analysis import analyze_apk


def show_connected_devices() -> None:
    """List connected devices using basic ``adb devices`` output."""
    try:
        output = device_discovery.check_connected_devices()
        devs = device_discovery.parse_devices_l(output)
    except RuntimeError as e:
        app_display.fail(str(e))
        return

    app_display.print_section("ADB Devices")
    if not devs:
        print("No devices attached.")
        return

    app_renderers.print_basic_device_table(devs)


def show_detailed_devices() -> None:
    """List devices with manufacturer and OS details."""
    try:
        detailed = device_discovery.list_detailed_devices()
    except RuntimeError as e:
        app_display.fail(str(e))
        return

    if not detailed:
        app_display.print_section("Connected Devices (Detailed)")
        print("No devices attached.")
        return

    report = ieee_report.format_device_inventory(detailed)
    print(report)


def list_installed_packages(serial: str) -> None:
    """Display packages installed on the device."""
    packages = package_scanner.inventory_packages(serial)
    app_display.print_section("Application Inventory")
    if not packages:
        print("No packages found.")
        return

    app_renderers.print_package_inventory(packages)


def scan_dangerous_permissions(serial: str) -> None:
    """Scan packages for dangerous permissions and display results."""
    try:
        risky = package_scanner.scan_for_dangerous_permissions(serial)
    except RuntimeError as e:
        app_display.fail(str(e))
        return

    app_display.print_section("Apps with Dangerous Permissions")
    if not risky:
        print("No apps requesting dangerous permissions found.")
        return
    app_renderers.print_permission_scan(risky)


def list_running_processes(serial: str) -> None:
    """List running processes on the device."""
    try:
        procs = process_listing.list_processes(serial)
    except RuntimeError as e:
        app_display.fail(str(e))
        return
    app_display.print_section("Running Processes")
    if not procs:
        print("No process data available.")
        return
    app_renderers.print_process_table(procs)


def analyze_apk_path() -> None:
    """Prompt for an APK path and run the static analyzer."""
    apk_path = input("Enter path to APK: ").strip()
    if not apk_path:
        print("Status: APK path is required.")
        return
    try:
        out = analyze_apk(apk_path)
    except Exception as e:  # pragma: no cover - broad catch for user feedback
        app_display.fail(f"Analysis failed: {e}")
        return
    print(f"Status: Static analysis completed. Results in {out}")
    _display_manifest_insights(out)


def analyze_installed_app(serial: str) -> None:
    """Select an installed app, pull its APK, and run static analysis."""
    try:
        packages = package_scanner.list_installed_packages(serial)
    except RuntimeError as e:
        app_display.fail(str(e))
        return
    if not packages:
        print("Status: No packages found.")
        return

    options = [
        (pkg + (" (Twitter)" if pkg == "com.twitter.android" else ""), pkg)
        for pkg in packages
    ]
    choice = app_menu_utils.show_menu(
        "Installed Packages",
        [label for label, _ in options],
        exit_label="Cancel",
        prompt="Select package",
    )
    if choice == 0:
        print("Status: No package selected.")
        return
    package = options[choice - 1][1]
    try:
        evidence = apk_extractor.acquire_apk(
            serial, package, dest_dir=f"output/{package}"
        )
        print("Status: Application package extracted successfully.")
        out = analyze_apk(str(evidence["artifact"]), outdir=f"output/{package}")
    except Exception as e:  # pragma: no cover
        app_display.fail(f"Analysis failed: {e}")
        return
    print(
        f"Status: Static analysis completed. Report at {out / 'report.json'}"
    )
    _display_manifest_insights(out)
    log = ieee_report.format_evidence_log([evidence])
    print(log)


def _display_manifest_insights(outdir: Path) -> None:
    """Load manifest-derived data and display tables."""
    try:
        components = json.loads((outdir / "components.json").read_text())
    except Exception:
        components = {}
    try:
        features = json.loads((outdir / "features.json").read_text())
    except Exception:
        features = []

    if features:
        app_display.print_section("Requested Features")
        app_renderers.print_feature_list(features)

    if components:
        for kind in ["activity", "service", "receiver", "provider"]:
            if components.get(kind):
                app_display.print_section(f"{kind.title()}s")
                app_renderers.print_component_table(components, kind)
