"""Utility to scan source files for potential secrets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

SECRET_PATTERN = re.compile(r"API[_-]?KEY|SECRET|TOKEN", re.IGNORECASE)


def scan_for_secrets(root: Path) -> List[str]:
    """Scan a directory tree for common secret keywords.

    Returns a list of "path:offset" strings for each finding.
    """
    findings: List[str] = []
    for file in root.rglob("*"):
        if not file.is_file():
            continue
        try:
            text = file.read_text(errors="ignore")
        except Exception:
            continue
        for match in SECRET_PATTERN.finditer(text):
            rel = file.relative_to(root)
            findings.append(f"{rel}:{match.start()}")
    return findings
