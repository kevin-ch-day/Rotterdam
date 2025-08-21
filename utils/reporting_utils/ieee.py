"""Minimal IEEE-style reporting utilities.

These helpers provide basic text formatting used throughout the CLI. They
intentionally avoid external dependencies and only implement the small subset
of functionality exercised in tests and command-line helpers.
"""
from __future__ import annotations

from typing import Iterable, List, Sequence

import json


def major_heading(text: str) -> str:
    """Return a top-level heading."""
    return f"# {text}\n"


def subsection_heading(text: str) -> str:
    """Return a second-level heading."""
    return f"## {text}\n"


def ieee_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    """Create a simple Markdown table.

    This is not a full IEEE implementation but suffices for CLI summaries.
    """
    col_widths = [len(h) for h in headers]
    table_rows: List[List[str]] = []
    for row in rows:
        r = [str(cell) for cell in row]
        table_rows.append(r)
        for i, cell in enumerate(r):
            col_widths[i] = max(col_widths[i], len(cell))
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * w for w in col_widths)
    body = "\n".join(
        " | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers)))
        for row in table_rows
    )
    return f"{header_line}\n{sep_line}\n{body}\n"


def format_evidence_log(evidence: Iterable[dict]) -> str:
    """Format evidence entries as a JSON string."""
    return json.dumps(list(evidence), indent=2)


def format_device_inventory(devices: Iterable[dict]) -> str:
    """Format a list of device dictionaries."""
    return json.dumps(list(devices), indent=2)


def format_package_inventory(packages: Iterable[dict]) -> str:
    """Format package information as JSON."""
    return json.dumps(list(packages), indent=2)


def format_risk_summary(summary: dict) -> str:
    """Return a simple risk summary string."""
    return json.dumps(summary, indent=2)


def format_yara_matches(matches: dict) -> str:
    """Format YARA matches for display."""
    return json.dumps(matches, indent=2)
