"""Utility to scan source files for potential secrets.

The module is intentionally structured so additional heuristics can be added
easily.  Each detection mechanism is implemented as a standalone *detector*
function which is invoked for every candidate file.  New detectors can be
registered in the ``DETECTORS`` list to extend the scanner without modifying
the main control flow.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Common keywords that often denote credentials or secrets
SECRET_PATTERN = re.compile(
    r"API[_-]?KEY|SECRET|TOKEN|PASSWORD|ACCESS[_-]?KEY|PRIVATE[_-]?KEY",
    re.IGNORECASE,
)

# Pattern for strings that might contain high entropy secrets such as keys
HIGH_ENTROPY_PATTERN = re.compile(r"[A-Za-z0-9+/=]{20,}")

ALLOWED_EXTENSIONS = {
    ".java",
    ".xml",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".md",
    ".properties",
    ".gradle",
    ".cfg",
    ".conf",
}

SIZE_LIMIT = 1 * 1024 * 1024  # 1MB


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """Represents a possible secret finding."""

    path: Path
    offset: int
    reason: str


# Detector signature: accepts file text and returns an iterable of findings.
Detector = Callable[[str, Path], Iterable[Finding]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _shannon_entropy(data: str) -> float:
    """Compute the Shannon entropy of a string."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def _is_text_file(path: Path) -> bool:
    """Return True if the file has an allowed text-based extension."""
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def _contains_nul_bytes(data: bytes) -> bool:
    """Quickly check if the byte content contains NUL bytes."""
    return b"\x00" in data


def _load_text(path: Path) -> str | None:
    """Return decoded text for *path* or ``None`` if it shouldn't be scanned."""
    try:
        if path.stat().st_size > SIZE_LIMIT:
            return None
        data = path.read_bytes()
    except Exception:
        return None
    if _contains_nul_bytes(data):
        return None
    return data.decode(errors="ignore")


def _iter_candidate_files(root: Path) -> Iterable[tuple[Path, str]]:
    """Yield ``(path, text)`` pairs for files that should be scanned."""
    for file in root.rglob("*"):
        if not file.is_file() or not _is_text_file(file):
            continue
        text = _load_text(file)
        if text is None:
            continue
        yield file, text


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def _keyword_detector(text: str, path: Path) -> Iterable[Finding]:
    """Find occurrences of common secret keywords."""
    for match in SECRET_PATTERN.finditer(text):
        yield Finding(path, match.start(), "keyword")


def _entropy_detector(text: str, path: Path) -> Iterable[Finding]:
    """Find strings with high entropy which may indicate secrets."""
    for match in HIGH_ENTROPY_PATTERN.finditer(text):
        token = match.group()
        if _shannon_entropy(token) > 4.5:
            yield Finding(path, match.start(), "entropy")


# List of registered detectors.  New heuristics can be appended here.
DETECTORS: List[Detector] = [_keyword_detector, _entropy_detector]


def _scan_text(path: Path, text: str) -> List[Finding]:
    """Run all detectors on the provided text."""
    findings: List[Finding] = []
    for detector in DETECTORS:
        findings.extend(detector(text, path))
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_for_secrets(root: Path) -> List[str]:
    """Scan a directory tree for potential secrets.

    Returns a list of ``"path:offset"`` strings for each finding. The function
    skips files larger than 1MB, binary files containing NUL bytes and only
    scans a predefined set of text-based extensions.
    """

    results: List[str] = []
    for path, text in _iter_candidate_files(root):
        for finding in _scan_text(path, text):
            rel = finding.path.relative_to(root)
            results.append(f"{rel}:{finding.offset}")
    return results


__all__ = [
    "Finding",
    "scan_for_secrets",
]

