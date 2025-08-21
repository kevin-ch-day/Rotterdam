from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from analysis import analyze_apk
from app_config import app_config
from devices import apk, packages
from utils.display_utils import display
from utils.reporting_utils import ieee

from ..prompts import prompt_existing_path
from .utils import action_context as _action_context
from .utils import logger


def analyze_apk_path() -> None:
    """Prompt for an APK path and run the static analyzer."""
    apk_path = prompt_existing_path(
        "Enter path to APK (or press Enter to cancel): ",
        "Status: APK analysis canceled.",
    )
    if not apk_path:
        return

    app_name = Path(apk_path).stem
    with _action_context("analyze_apk_path", apk_path=apk_path):
        logger.info("analyze_apk_path", extra={"apk": apk_path})
        outdir = app_config.OUTPUT_DIR / app_config.ts()
        try:
            out = analyze_apk(apk_path, outdir=outdir)
        except Exception as e:  # pragma: no cover - broad catch for user feedback
            logger.exception("analysis failed")
            display.fail(f"Analysis failed: {e}")
            return
        report_path = out / "report.json"
        # Database storage has been removed for the MVP, so the report path is
        # not persisted.  Future iterations may reintroduce this functionality.
        logger.info("analysis completed", extra={"output": str(out)})
        print(f"Status: Static analysis completed. Report at {report_path}")
        _display_manifest_insights(out)


def analyze_installed_app(serial: str) -> None:
    """Select an installed app, pull its APK, and run static analysis."""
    with _action_context("analyze_installed_app", device_serial=serial):
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
            (pkg + (" (Twitter)" if pkg == "com.twitter.android" else ""), pkg) for pkg in pkgs
        ]
        choice = display.show_menu(
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

        outdir = app_config.OUTPUT_DIR / app_config.ts()
        try:
            evidence = apk.acquire_apk(serial, package, dest_dir=str(outdir))
            apk_path = str(evidence["artifact"])
            logger.info("apk extracted", extra={"output": str(outdir)})
            print("Status: Application package extracted successfully.")
            with _action_context("analyze_installed_app", device_serial=serial, apk_path=apk_path):
                out = analyze_apk(apk_path, outdir=outdir)
        except Exception as e:  # pragma: no cover
            logger.exception("analysis failed")
            display.fail(f"Analysis failed: {e}")
            return

        report_path = out / "report.json"
        # Storage of analysis metadata is temporarily disabled in the CLI-only
        # phase.
        logger.info("analysis completed", extra={"report": str(report_path)})
        print(f"Status: Static analysis completed. Report at {report_path}")
        _display_manifest_insights(out)
        log = ieee.format_evidence_log([evidence])
        print(log)


def sandbox_analyze_apk() -> None:
    """Stub for removed sandbox analysis functionality."""
    print("Sandbox features are disabled.")


def explore_installed_app(serial: str) -> None:
    """Stub for removed sandbox UI exploration functionality."""
    print("Sandbox features are disabled.")


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
        rows = [[f.get("name", ""), "yes" if f.get("required") else "no"] for f in features]
        display.print_table(rows, headers=["Feature", "Required"])

    if components:
        for kind in ["activity", "service", "receiver", "provider"]:
            if components.get(kind):
                display.print_section(f"{kind.title()}s")
                rows = [
                    [
                        c.get("name", ""),
                        "yes" if c.get("exported") else "no",
                        c.get("permission", ""),
                    ]
                    for c in components.get(kind, [])
                ]
                display.print_table(rows, headers=["Name", "Exported", "Permission"])

    if metrics:
        display.print_section("Derived Metrics")
        rows = [[k, str(v)] for k, v in sorted(metrics.items()) if not isinstance(v, dict)]
        display.print_table(rows, headers=["Metric", "Value"])
        prefix_counts = metrics.get("permission_prefix_counts")
        if prefix_counts:
            display.print_section("Permission Patterns")
            rows = [
                [p, str(c)] for p, c in sorted(prefix_counts.items(), key=lambda x: (-x[1], x[0]))
            ]
            display.print_table(rows, headers=["Prefix", "Count"])

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
