"""Simplified IEEE reporting utilities.

This module provides placeholder implementations of the IEEE reporting
helpers used throughout the codebase. The original implementation is
unavailable in this environment, so these functions provide minimal
behavior sufficient for tests.
"""

from __future__ import annotations

from typing import Iterable, Sequence


def format_device_inventory(*args, **kwargs) -> str:
    """Return a placeholder device inventory report."""
    return ""


def format_evidence_log(*args, **kwargs) -> str:
    """Return a placeholder evidence log."""
    return ""


def format_package_inventory(*args, **kwargs) -> str:
    """Return a placeholder package inventory report."""
    return ""


def format_risk_summary(*args, **kwargs) -> str:
    """Return a placeholder risk summary."""
    return ""


def format_yara_matches(*args, **kwargs) -> str:
    """Return a placeholder YARA match report."""
    return ""


def ieee_table(rows: Sequence[Sequence[str]]) -> str:
    """Create a simple table from the provided rows.

    Each row is joined by ``\t`` and terminated with a newline.
    """
    return "\n".join("\t".join(map(str, row)) for row in rows)


def major_heading(text: str) -> str:
    """Format ``text`` as a major heading."""
    return text.upper()


def subsection_heading(text: str) -> str:
    """Format ``text`` as a subsection heading."""
    return text
