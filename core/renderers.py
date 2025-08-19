#!/usr/bin/env python3
"""Reusable table renderers for common CLI outputs."""

from __future__ import annotations
"""Rendering helpers for tabular and list-based outputs."""

from typing import Iterable, List, Any, Dict

from . import display


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
    display.print_table(
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
    display.print_table(
        rows,
        headers=["Package", "Version", "Installer", "High-Value"],
    )


def print_permission_scan(results: Iterable[Dict[str, Any]]) -> None:
    """Print packages that request risky permissions."""
    rows: List[List[str]] = []
    for r in results:
        rendered_perms: List[str] = []
        for p in r.get("permissions", []):
            meta: List[str] = [p.get("category", "")]
            if p.get("granted"):
                meta.append("granted")
            if p.get("mode"):
                meta.append(p["mode"])
            rendered_perms.append(f"{p['name']} ({','.join(m for m in meta if m)})")
        perms = ", ".join(rendered_perms)
        flags = ", ".join(r.get("risk_flags", []))
        rows.append([r.get("package", ""), perms, flags])
    display.print_table(rows, headers=["Package", "Permissions", "Risk Flags"])


# ---------------------------------------------------------------------------
# Process listings
# ---------------------------------------------------------------------------

def print_process_table(processes: Iterable[Dict[str, Any]]) -> None:
    """Print a table of running processes."""
    rows: List[List[str]] = [
        [p.get("pid", ""), p.get("user", ""), p.get("name", "")] for p in processes
    ]
    display.print_table(rows, headers=["PID", "User", "Name"])


# ---------------------------------------------------------------------------
# Manifest analysis renderers
# ---------------------------------------------------------------------------

def print_feature_list(features: Iterable[Dict[str, Any]]) -> None:
    """Print requested hardware/software features."""
    rows: List[List[str]] = [
        [f.get("name", ""), "yes" if f.get("required") else "no"]
        for f in features
    ]
    display.print_table(rows, headers=["Feature", "Required"])


def print_component_table(
    components: Dict[str, List[Dict[str, Any]]], kind: str
) -> None:
    """Print details for a specific component kind (activity/service/etc)."""
    rows: List[List[str]] = [
        [c.get("name", ""), "yes" if c.get("exported") else "no", c.get("permission", "")]
        for c in components.get(kind, [])
    ]
    display.print_table(
        rows,
        headers=["Name", "Exported", "Permission"],
    )


# ---------------------------------------------------------------------------
# Metrics and pattern summaries
# ---------------------------------------------------------------------------

def print_metric_table(metrics: Dict[str, Any]) -> None:
    """Print key/value metric pairs."""
    rows = [[k, str(v)] for k, v in sorted(metrics.items()) if not isinstance(v, dict)]
    display.print_table(rows, headers=["Metric", "Value"])


def print_prefix_summary(prefix_counts: Dict[str, int]) -> None:
    """Print summarized permission prefix counts."""
    rows = [
        [p, str(c)] for p, c in sorted(prefix_counts.items(), key=lambda x: (-x[1], x[0]))
    ]
    display.print_table(rows, headers=["Prefix", "Count"])
