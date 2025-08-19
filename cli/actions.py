"""High-level device-related actions for the CLI.

These functions wrap lower-level utilities and present formatted
output for the user interface.
"""

from __future__ import annotations

import json
from pathlib import Path

from core import display, menu, renderers, config
from .prompts import prompt_existing_path
from reports import ieee
from devices import (
    discovery,
    packages,
    apk,
    processes,
)
from analysis import analyze_apk
from sandbox import run_analysis as sandbox_analyze, compute_runtime_metrics
from sandbox import ui_driver


def show_connected_devices() -> None:
    """List connected devices using basic ``adb devices`` output."""
    try:
        output = discovery.check_connected_devices()
        devs = discovery.parse_devices_l(output)
    except RuntimeError as e:
        display.fail(str(e))
        return

    display.print_section("ADB Devices")
    if not devs:
        print("No devices attached.")
        return

    renderers.print_basic_device_table(devs)


def show_detailed_devices() -> None:
    """List devices with manufacturer and OS details."""
    try:
        detailed = discovery.list_detailed_devices()
    except RuntimeError as e:
        display.fail(str(e))
        return

    if not detailed:
        display.print_section("Connected Devices (Detailed)")
        print("No devices attached.")
        return

    report = ieee.format_device_inventory(detailed)
    print(report)


def list_installed_packages(serial: str) -> None:
    """Display packages installed on the device."""
    pkg_info = packages.inventory_packages(serial)
    display.print_section("Application Inventory")
    if not pkg_info:
        print("No packages found.")
        return

    renderers.print_package_inventory(pkg_info)


def scan_dangerous_permissions(serial: str) -> None:
    """Scan packages for dangerous permissions and display results."""
    try:
        risky = packages.scan_for_dangerous_permissions(serial)
    except RuntimeError as e:
        display.fail(str(e))
        return

    display.print_section("Apps with Dangerous Permissions")
    if not risky:
        print("No apps requesting dangerous permissions found.")
        return
    renderers.print_permission_scan(risky)


def list_running_processes(serial: str) -> None:
    """List running processes on the device."""
    try:
        procs = processes.list_processes(serial)
    except RuntimeError as e:
        display.fail(str(e))
        return
    display.print_section("Running Processes")
    if not procs:
        print("No process data available.")
        return
    renderers.print_process_table(procs)


def analyze_apk_path() -> None:
    """Prompt for an APK path and run the static analyzer."""
    apk_path = prompt_existing_path(
        "Enter path to APK (or press Enter to cancel): ",
        "Status: APK analysis canceled.",
    )
    if not apk_path:
        return

    try:
        out = analyze_apk(apk_path)
    except Exception as e:  # pragma: no cover - broad catch for user feedback
        display.fail(f"Analysis failed: {e}")
        return
    print(f"Status: Static analysis completed. Results in {out}")
    _display_manifest_insights(out)


def analyze_installed_app(serial: str) -> None:
    """Select an installed app, pull its APK, and run static analysis."""
    try:
        pkgs = packages.list_installed_packages(serial)
    except RuntimeError as e:
        display.fail(str(e))
        return
    if not pkgs:
        print("Status: No packages found.")
        return

    options = [
        (pkg + (" (Twitter)" if pkg == "com.twitter.android" else ""), pkg)
        for pkg in pkgs
    ]
    choice = menu.show_menu(
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
        evidence = apk.acquire_apk(
            serial, package, dest_dir=f"output/{package}"
        )
        print("Status: Application package extracted successfully.")
        out = analyze_apk(str(evidence["artifact"]), outdir=f"output/{package}")
    except Exception as e:  # pragma: no cover
        display.fail(f"Analysis failed: {e}")
        return
    print(
        f"Status: Static analysis completed. Report at {out / 'report.json'}"
    )
    _display_manifest_insights(out)
    log = ieee.format_evidence_log([evidence])
    print(log)


def sandbox_analyze_apk() -> None:
    """Prompt for an APK path and run sandbox analysis."""
    apk_path = prompt_existing_path(
        "Enter path to APK (or press Enter to cancel): ",
        "Status: Sandbox analysis canceled.",
    )
    if not apk_path:
        return

    outdir = config.OUTPUT_DIR / f"{Path(apk_path).stem}_sandbox"
    try:
        results = sandbox_analyze(apk_path, outdir)
    except Exception as e:  # pragma: no cover - broad catch for user feedback
        display.fail(f"Sandbox analysis failed: {e}")
        return

    print(f"Status: Sandbox analysis completed. Results in {outdir}")

    perms = results.get("permissions", [])
    if perms:
        display.print_section("Observed Permissions")
        for p in perms:
            print(p)

    nets = results.get("network", [])
    if nets:
        display.print_section("Network Activity")
        for n in nets:
            print(f"{n.get('protocol', '')} -> {n.get('destination', '')}")


def explore_installed_app(serial: str) -> None:
    """Select an installed package and run automated UI exploration."""
    try:
        pkgs = packages.list_installed_packages(serial)
    except RuntimeError as e:
        display.fail(str(e))
        return
    if not pkgs:
        print("Status: No packages found.")
        return

    choice = menu.show_menu(
        "Installed Packages",
        pkgs,
        exit_label="Cancel",
        prompt="Select package",
    )
    if choice == 0:
        print("Status: No package selected.")
        return
    package = pkgs[choice - 1]
    activities = ui_driver.run_monkey(serial, package)
    metrics = compute_runtime_metrics([], [], [], activities)

    display.print_section("Visited Activities")
    if metrics["activities"]:
        for act in metrics["activities"]:
            print(act)
        print(f"Total: {metrics['activity_count']}")
    else:
        print("No activity coverage recorded.")


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
    try:
        report = json.loads((outdir / "report.json").read_text())
    except Exception:
        report = {}
    metrics = report.get("metrics", {})
    diff = report.get("diff", {})

    if features:
        display.print_section("Requested Features")
        renderers.print_feature_list(features)

    if components:
        for kind in ["activity", "service", "receiver", "provider"]:
            if components.get(kind):
                display.print_section(f"{kind.title()}s")
                renderers.print_component_table(components, kind)

    if metrics:
        display.print_section("Derived Metrics")
        renderers.print_metric_table(metrics)
        prefix_counts = metrics.get("permission_prefix_counts")
        if prefix_counts:
            display.print_section("Permission Patterns")
            renderers.print_prefix_summary(prefix_counts)
    if diff:
        display.print_section("Differences from Previous Version")
        added_perms = diff.get("added_permissions", [])
        removed_perms = diff.get("removed_permissions", [])
        if added_perms:
            print("Added permissions: " + ", ".join(added_perms))
        if removed_perms:
            print("Removed permissions: " + ", ".join(removed_perms))
        for kind, names in diff.get("added_components", {}).items():
            if names:
                print(f"Added {kind.title()}s: {', '.join(names)}")
        for kind, names in diff.get("removed_components", {}).items():
            if names:
                print(f"Removed {kind.title()}s: {', '.join(names)}")
