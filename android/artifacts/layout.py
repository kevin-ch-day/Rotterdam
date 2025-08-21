"""Helpers for computing canonical artifact paths.

The layout groups all analysis output under ``scans/<scan_id>/``::

    scans/<scan_id>/
      apks/app.apk
      decomp/java.zip
      decomp/smali.zip
      facts/*.json
      findings.json
      score.json
      reports/{report.json, report.html, report.pdf}
      logs/pipeline.log
"""

from __future__ import annotations

from pathlib import Path


def scan_root(base: Path, scan_id: str) -> Path:
    """Return the root directory for ``scan_id`` under ``base``."""
    return base / "scans" / scan_id


def apk_path(root: Path) -> Path:
    return root / "apks" / "app.apk"


def java_decomp(root: Path) -> Path:
    return root / "decomp" / "java.zip"


def smali_decomp(root: Path) -> Path:
    return root / "decomp" / "smali.zip"


def facts_dir(root: Path) -> Path:
    return root / "facts"


def findings_path(root: Path) -> Path:
    return root / "findings.json"


def score_path(root: Path) -> Path:
    return root / "score.json"


def report_dir(root: Path) -> Path:
    return root / "reports"


def log_path(root: Path) -> Path:
    return root / "logs" / "pipeline.log"


__all__ = [
    "scan_root",
    "apk_path",
    "java_decomp",
    "smali_decomp",
    "facts_dir",
    "findings_path",
    "score_path",
    "report_dir",
    "log_path",
]

