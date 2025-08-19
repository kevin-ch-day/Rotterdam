#!/usr/bin/env python3
"""Reusable table renderers for common CLI outputs."""

from __future__ import annotations

from typing import Iterable, List, Any, Dict

from . import app_display


# ---------------------------------------------------------------------------
# Device listings
# ---------------------------------------------------------------------------

def print_basic_device_table(devices: Iterable[Dict[str, Any]]) -> None:
    """Print a simple table of connected devices."""
    rows: List[List[str]] = [
        [
            d.get("serial", ""),
            d.get("state", ""),
            d.get("product", "-"),
            d.get("model", "-"),
            d.get("device", "-"),
            d.get("transport_id", d.get("transport", "-")),
        ]
        for d in devices
    ]
    app_display.print_table(
        rows,
        headers=["Serial", "State", "Product", "Model", "Device", "Transport"],
    )


# ---------------------------------------------------------------------------
# Package and permission reporting
# ---------------------------------------------------------------------------

def print_package_inventory(packages: Iterable[Dict[str, Any]]) -> None:
    """Print installed package inventory."""
    rows: List[List[str]] = [
        [
            p.get("package", ""),
            p.get("version_name", ""),
            p.get("installer", ""),
            "yes" if p.get("high_value") else "no",
        ]
        for p in packages
    ]
    app_display.print_table(
        rows,
        headers=["Package", "Version", "Installer", "High-Value"],
    )


def print_permission_scan(results: Iterable[Dict[str, Any]]) -> None:
    """Print packages that request dangerous permissions."""
    rows: List[List[str]] = [
        [r.get("package", ""), ", ".join(r.get("permissions", []))]
        for r in results
    ]
    app_display.print_table(rows, headers=["Package", "Permissions"])


# ---------------------------------------------------------------------------
# Process listings
# ---------------------------------------------------------------------------

def print_process_table(processes: Iterable[Dict[str, Any]]) -> None:
    """Print a table of running processes."""
    rows: List[List[str]] = [
        [p.get("pid", ""), p.get("user", ""), p.get("name", "")] for p in processes
    ]
    app_display.print_table(rows, headers=["PID", "User", "Name"])


# ---------------------------------------------------------------------------
# Manifest analysis renderers
# ---------------------------------------------------------------------------

def print_feature_list(features: Iterable[Dict[str, Any]]) -> None:
    """Print requested hardware/software features."""
    rows: List[List[str]] = [
        [f.get("name", ""), "yes" if f.get("required") else "no"]
        for f in features
    ]
    app_display.print_table(rows, headers=["Feature", "Required"])


def print_component_table(
    components: Dict[str, List[Dict[str, Any]]], kind: str
) -> None:
    """Print details for a specific component kind (activity/service/etc)."""
    rows: List[List[str]] = [
        [c.get("name", ""), "yes" if c.get("exported") else "no", c.get("permission", "")]
        for c in components.get(kind, [])
    ]
    app_display.print_table(
        rows,
        headers=["Name", "Exported", "Permission"],
    )
