#!/usr/bin/env python3
"""Minimal IEEE-style reporting utilities.

These helpers provide basic text and table formatting used throughout the CLI.
They intentionally avoid heavy dependencies and provide both human-readable
ASCII tables and JSON-structured outputs where appropriate.
"""

from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Sequence

from utils.display_utils import display

if TYPE_CHECKING:  # type checking only
    from devices.types import DeviceInfo
else:  # runtime fallback
    DeviceInfo = Any  # type: ignore


# -----------------------------
# Headings
# -----------------------------


def major_heading(text: str) -> str:
    """Return a top-level heading."""
    return f"# {text}\n"


def subsection_heading(text: str) -> str:
    """Return a second-level heading."""
    return f"## {text}\n"


# -----------------------------
# Tables
# -----------------------------


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


# -----------------------------
# JSON / Structured Logs
# -----------------------------


def format_evidence_log(evidence: Iterable[Dict[str, Any]]) -> str:
    """Format evidence entries as JSON."""
    return json.dumps(list(evidence), indent=2)


def format_package_inventory(packages: Iterable[Dict[str, Any]]) -> str:
    """Format package information as JSON."""
    return json.dumps(list(packages), indent=2)


def format_risk_summary(summary: Dict[str, Any]) -> str:
    """Return a simple risk summary string."""
    return json.dumps(summary, indent=2)


def format_yara_matches(matches: Dict[str, Any]) -> str:
    """Format YARA matches for display."""
    return json.dumps(matches, indent=2)
