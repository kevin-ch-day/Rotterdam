#!/usr/bin/env python3
"""Utilities for rendering findings in an IEEE-style report."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from typing import Any, Dict, Iterable, List, Sequence

from core import table

_ROMAN_MAP = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]


def _roman(num: int) -> str:
    """Return the uppercase Roman numeral for ``num`` (1 <= num < 4000)."""
    if num <= 0 or num >= 4000:
        raise ValueError("number out of range for Roman numeral")
    res = []
    n = num
    for val, sym in _ROMAN_MAP:
        while n >= val:
            res.append(sym)
            n -= val
    return "".join(res)


def major_heading(title: str, number: int) -> str:
    """Return an uppercase ``SECTION`` heading with a Roman numeral index."""
    numeral = _roman(number)
    return f"SECTION {numeral}: {title.upper()}"


def subsection_heading(title: str, section: int, letter: str) -> str:
    """Return a subsection heading like ``I.A – Title``."""
    numeral = _roman(section)
    return f"{numeral}.{letter} – {title}".strip()


def _table_to_str(rows: Iterable[Sequence[Any]], headers: Sequence[str]) -> str:
    """Render the existing ASCII table utility to a string."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        table.print_table(rows, headers=headers)
    return buf.getvalue().rstrip()


def ieee_table(
    title: str, headers: Sequence[str], rows: Iterable[Sequence[Any]], table_number: int
) -> str:
    """Return a table with an IEEE-style caption."""
    caption = f"Table {_roman(table_number)}. {title}"
    table_str = _table_to_str(rows, headers)
    return f"{caption}\n{table_str}"


def format_device_inventory(devices: List[dict[str, Any]]) -> str:
    """Format a device inventory into a section with headings, table, and observation."""
    heading = major_heading("Device Enumeration", 1)
    sub = subsection_heading("Detecting Connected Devices", 1, "A")
    intro = "The system enumerated connected Android devices and assessed trust posture."
    rows = [
        [d.get("serial", ""), d.get("model", ""), d.get("android_release", ""), d.get("trust", "")]
        for d in devices
    ]
    table = ieee_table(
        "Connected Devices",
        ["Serial", "Model", "Android", "Trust"],
        rows,
        1,
    )
    obs = (
        "Observation: The system detected {} device(s) suitable for analysis.".format(len(devices))
        if devices
        else "Observation: No devices were detected."
    )
    return f"{heading}\n{sub}\n{intro}\n\n{table}\n\n{obs}"


def format_package_inventory(packages: List[dict[str, Any]]) -> str:
    """Format application inventory with headings, table, and observation."""
    heading = major_heading("Application Inventory", 2)
    sub = subsection_heading("Application Discovery", 2, "A")
    intro = "Installed packages were cataloged with version, installer source, and high-value flag."
    rows = [
        [
            p.get("package", ""),
            p.get("version_name", ""),
            p.get("installer", ""),
            "yes" if p.get("high_value") else "no",
        ]
        for p in packages
    ]
    table = ieee_table(
        "Installed Applications",
        ["Package", "Version", "Installer", "High-Value"],
        rows,
        2,
    )
    obs = (
        "Observation: Package inventory produced {} candidate application(s) for review.".format(
            len(packages)
        )
        if packages
        else "Observation: No packages were enumerated."
    )
    return f"{heading}\n{sub}\n{intro}\n\n{table}\n\n{obs}"


def format_evidence_log(entries: List[dict[str, str]]) -> str:
    """Render an evidence log appendix with headings, table, and observation."""
    heading = major_heading("Evidence Log", 3)
    sub = subsection_heading("Acquisition Evidence", 3, "A")
    intro = "Chain-of-custody records for collected artifacts are listed below."
    rows = [
        [e.get("artifact", ""), e.get("sha256", ""), e.get("timestamp", ""), e.get("operator", "")]
        for e in entries
    ]
    table = ieee_table(
        "Acquisition Evidence",
        ["Artifact", "SHA-256", "Timestamp", "Operator"],
        rows,
        3,
    )
    obs = (
        "Observation: Chain-of-custody records captured for {} artifact(s).".format(len(entries))
        if entries
        else "Observation: No evidence entries were recorded."
    )
    return f"{heading}\n{sub}\n{intro}\n\n{table}\n\n{obs}"


def format_risk_summary(risk: dict[str, Any]) -> str:
    """Render a risk assessment section."""
    heading = major_heading("Risk Assessment", 4)
    sub = subsection_heading("Aggregated Risk Score", 4, "A")
    score = risk.get("score", 0.0)
    rationale = risk.get("rationale", "")
    breakdown_items = risk.get("breakdown", {})
    rows = [(k.replace("_", " "), f"{v:.2f}") for k, v in breakdown_items.items()]
    table = ieee_table("Risk Breakdown", ["Metric", "Contribution"], rows, 4)
    obs = f"Observation: Overall risk score is {score:.2f}."
    return f"{heading}\n{sub}\n{rationale}\n\n{table}\n\n{obs}"


def format_yara_matches(matches: Dict[str, List[str]]) -> str:
    """Render YARA scan results."""
    heading = major_heading("YARA Scan", 5)
    sub = subsection_heading("Rule Matches", 5, "A")
    rows = [(path, ", ".join(rules)) for path, rules in sorted(matches.items())]
    table = ieee_table("YARA Matches", ["File", "Rules"], rows, 5)
    obs = (
        "Observation: YARA identified {} file(s) with rule matches.".format(len(rows))
        if rows
        else "Observation: No YARA matches were found."
    )
    return f"{heading}\n{sub}\n{table}\n\n{obs}"
