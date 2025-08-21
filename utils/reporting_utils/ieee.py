#!/usr/bin/env python3
"""Minimal IEEE-style reporting helpers."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Sequence

from utils.display_utils import display

if TYPE_CHECKING:  # import for type checking only
    from devices.types import DeviceInfo
else:  # runtime fallback
    DeviceInfo = Any  # type: ignore


def ieee_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Render an ASCII table and return it as a string."""
    buf = StringIO()
    with redirect_stdout(buf):
        display.print_table(rows, headers=headers)
    return buf.getvalue().rstrip()


def format_device_inventory(devices: List[DeviceInfo]) -> str:
    """Return a table summarizing connected devices."""
    rows = [
        [
            getattr(d, "serial", "") or "-",
            getattr(d, "state", "") or "-",
            getattr(d, "product", "") or "-",
            getattr(d, "model", "") or "-",
            getattr(d, "device", "") or "-",
            getattr(d, "transport_id", getattr(d, "transport", "-")) or "-",
        ]
        for d in devices
    ]
    headers = ["Serial", "State", "Product", "Model", "Device", "Transport"]
    return ieee_table(headers, rows)


def format_evidence_log(entries: Iterable[Dict[str, Any]]) -> str:
    """Render a simple evidence log."""
    lines = ["Evidence Log"]
    for e in entries:
        name = e.get("name", "artifact")
        path = e.get("artifact", "")
        lines.append(f"- {name}: {path}")
    return "\n".join(lines)


def format_package_inventory(packages: Iterable[Dict[str, Any]]) -> str:
    """Placeholder package inventory formatter."""
    lines = ["Package Inventory"]
    for p in packages:
        lines.append(p.get("package", ""))
    return "\n".join(lines)


def format_risk_summary(summary: Dict[str, Any]) -> str:
    """Placeholder risk summary formatter."""
    return "\n".join(f"{k}: {v}" for k, v in summary.items())


def format_yara_matches(matches: Iterable[Dict[str, Any]]) -> str:
    """Placeholder YARA matches formatter."""
    lines = ["YARA Matches"]
    for m in matches:
        lines.append(m.get("rule", ""))
    return "\n".join(lines)


def major_heading(text: str) -> str:
    """Return a major heading string."""
    return text.upper()


def subsection_heading(text: str) -> str:
    """Return a subsection heading string."""
    return text
