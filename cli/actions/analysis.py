from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from core import config, menu, renderers
from devices import apk, packages
from analysis import analyze_apk
from sandbox import run_analysis as sandbox_analyze, compute_runtime_metrics
from sandbox import ui_driver
from reports import ieee
from storage.repository import AnalysisRepository
from utils.display_utils import display

from ..prompts import prompt_existing_path
from .utils import action_context as _action_context, logger


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

        options = [(pkg + (" (Twitter)" if pkg == "com.twitter.android" else ""), pkg) for pkg in pkgs]
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

        outdir = config.OUTPUT_DIR / config.ts()
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
    with _action_context("sandbox_analyze_apk", apk_path=apk_path):
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
    with _action_context("explore_installed_app", device_serial=serial):
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

