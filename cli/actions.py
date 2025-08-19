"""High-level device-related actions for the CLI.

These functions wrap lower-level utilities and present formatted
output for the user interface.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, Optional
import argparse

from core import display, menu, renderers, config
from core.diagnostics import SystemDoctor, BinaryCheck, ModuleCheck
from .prompts import prompt_existing_path
from reports import ieee
from devices import (
    discovery,
    packages,
    apk,
    processes,
    selection,
)
from analysis import analyze_apk
from sandbox import run_analysis as sandbox_analyze, compute_runtime_metrics
from sandbox import ui_driver
from storage.repository import AnalysisRepository

# Optional logging integration
try:
    from logging_config import get_logger, log_context  # type: ignore
    logger = get_logger(__name__)  # type: ignore
except Exception:  # pragma: no cover
    import logging

    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    @contextmanager
    def log_context(**_: Any):  # type: ignore
        yield


def run_doctor() -> None:
    """Check availability of required binaries and Python modules."""

    checks = [
        *(BinaryCheck(b) for b in ["adb", "aapt2", "apktool", "jadx", "yara", "java"]),
        *(ModuleCheck(m) for m in [
            "androguard",
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "mysql.connector",
        ]),
    ]

    doctor = SystemDoctor(checks)
    results = doctor.run()

    display.print_section("Binary Dependencies")
    for res in (r for r in results if r.category == "binary"):
        if res.ok:
            display.good(f"{res.name} : {res.detail}")
        else:
            display.fail(f"{res.name} : {res.detail}")

    display.print_section("Python Modules")
    for res in (r for r in results if r.category == "module"):
        if res.ok:
            display.good(f"{res.name} : {res.detail}")
        else:
            display.fail(f"{res.name} : {res.detail}")

    if doctor.has_issues:
        display.warn("One or more diagnostics failed. Review the flags above.")


def show_connected_devices() -> None:
    """List connected devices using basic ``adb devices`` output."""
    logger.info("show_connected_devices")
    try:
        output = discovery.check_connected_devices()
        devs = discovery.parse_devices_l(output)  # keep API as defined in devices.discovery
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
    with log_context(device=serial):
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
    """Scan packages for risky permissions and display results."""
    with log_context(device=serial):
        logger.info("scan_dangerous_permissions")
        try:
            risky = packages.scan_for_dangerous_permissions(serial)
        except RuntimeError as e:
            logger.exception("permission scan failed")
            display.fail(str(e))
            return

        display.print_section("Apps with Risky Permissions")
        if not risky:
            logger.info("no apps with dangerous permissions")
            print("No apps requesting dangerous permissions found.")
            return
        renderers.print_permission_scan(risky)
        out_dir = Path("output")
        packages.export_permission_scan(
            risky,
            json_path=out_dir / "permission_scan.json",
            csv_path=out_dir / "permission_scan.csv",
        )


def scan_for_devices() -> None:
    """Rescan ADB for devices and display the results."""
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
    with log_context(device=serial):
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


def analyze_apk_path() -> None:
    """Prompt for an APK path and run the static analyzer."""
    apk_path = prompt_existing_path(
        "Enter path to APK (or press Enter to cancel): ",
        "Status: APK analysis canceled.",
    )
    if not apk_path:
        return

    app_name = Path(apk_path).stem
    with log_context(app=app_name):
        logger.info("analyze_apk_path", extra={"apk": apk_path})
        outdir = config.OUTPUT_DIR / config.ts()
        try:
            out = analyze_apk(apk_path, outdir=outdir)
        except Exception as e:  # pragma: no cover - broad catch for user feedback
            logger.exception("analysis failed")
            display.fail(f"Analysis failed: {e}")
            return
        report_path = out / "report.json"
        try:
            AnalysisRepository().upsert(app_name, str(report_path))
        except Exception:
            logger.exception("failed to record analysis")
        logger.info("analysis completed", extra={"output": str(out)})
        print(f"Status: Static analysis completed. Report at {report_path}")
        _display_manifest_insights(out)


def analyze_installed_app(serial: str) -> None:
    """Select an installed app, pull its APK, and run static analysis."""
    with log_context(device=serial):
        logger.info("analyze_installed_app")
        try:
            pkgs = packages.list_installed_packages(serial)
        except RuntimeError as e:
            logger.exception("failed to list installed packages")
            display.fail(str(e))
            return
        if not pkgs:
            logger.info("no packages found")
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
            logger.info("no package selected")
            print("Status: No package selected.")
            return
        package = options[choice - 1][1]

        with log_context(app=package):
            outdir = config.OUTPUT_DIR / config.ts()
            try:
                evidence = apk.acquire_apk(serial, package, dest_dir=str(outdir))
                logger.info("apk extracted", extra={"output": str(outdir)})
                print("Status: Application package extracted successfully.")
                out = analyze_apk(str(evidence["artifact"]), outdir=outdir)
            except Exception as e:  # pragma: no cover
                logger.exception("analysis failed")
                display.fail(f"Analysis failed: {e}")
                return
            report_path = out / "report.json"
            try:
                AnalysisRepository().upsert(package, str(report_path))
            except Exception:
                logger.exception("failed to record analysis")
            logger.info("analysis completed", extra={"report": str(report_path)})
            print(f"Status: Static analysis completed. Report at {report_path}")
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

    app_name = Path(apk_path).stem
    outdir = config.OUTPUT_DIR / config.ts()
    with log_context(app=app_name):
        logger.info("sandbox_analyze_apk", extra={"apk": apk_path})
        try:
            results = sandbox_analyze(apk_path, outdir)
        except Exception as e:  # pragma: no cover - broad catch for user feedback
            logger.exception("sandbox analysis failed")
            display.fail(f"Sandbox analysis failed: {e}")
            return

        report_path = outdir / "metrics.json"
        try:
            target_path = report_path if report_path.exists() else outdir
            AnalysisRepository().upsert(app_name, str(target_path))
        except Exception:
            logger.exception("failed to record analysis")
        logger.info("sandbox analysis completed", extra={"output": str(outdir)})
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
    if metrics.get("activities"):
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

    metrics: Dict[str, Any] = report.get("metrics", {})
    diff: Dict[str, Any] = report.get("diff", {})

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


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the API server using uvicorn."""
    import uvicorn

    uvicorn.run("server:app", host=host, port=port)


def main(argv: list[str] | None = None) -> None:
    """Minimal CLI for auxiliary commands."""
    parser = argparse.ArgumentParser(description="Rotterdam utilities")
    sub = parser.add_subparsers(dest="cmd")

    p_serve = sub.add_parser("serve", help="start API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    p_list = sub.add_parser("list-packages", help="list installed packages")
    p_list.add_argument("serial", help="device serial")
    p_list.add_argument("--user", action="store_true", help="show only user apps")
    p_list.add_argument("--system", action="store_true", help="show only system apps")
    p_list.add_argument(
        "--high-value", action="store_true", help="show only high-value apps"
    )
    p_list.add_argument("--regex", help="filter packages by regex")
    p_list.add_argument("--csv", help="export results to CSV at path")
    p_list.add_argument("--json", dest="json_path", help="export results to JSON")
    p_list.add_argument("--limit", type=int, help="limit number of results")

    args = parser.parse_args(argv)
    if args.cmd == "serve":
        run_server(args.host, args.port)
    elif args.cmd == "list-packages":
        list_installed_packages(
            args.serial,
            user=args.user,
            system=args.system,
            high_value=args.high_value,
            regex=args.regex,
            csv_path=args.csv,
            json_path=args.json_path,
            limit=args.limit,
        )
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
