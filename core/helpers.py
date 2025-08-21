#!/usr/bin/env python3
# File: core/helpers.py
# helpers.py
"""
General-purpose helper functions for Android Tool.
Not specific to display, menus, or config.
"""

from __future__ import annotations
import hashlib


def format_bytes(n: int) -> str:
    """
    Convert a byte count into a human-friendly string.
    Example: 1024 -> '1.00 KB'
    """
    if n < 0:
        raise ValueError("Byte size cannot be negative")

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.2f} {u}"
        size /= 1024.0
    return f"{size:.2f} {units[-1]}"


def truncate_middle(s: str, max_len: int) -> str:
    """
    Truncate a long string in the middle with an ellipsis.
    Example: '/very/long/path/file.txt' -> '/very/lo…file.txt'
    """
    if len(s) <= max_len or max_len < 5:
        return s if len(s) <= max_len else s[:max_len]
    half = (max_len - 1) // 2
    return s[:half] + "…" + s[-(max_len - half - 1):]


def sha256sum(data: bytes) -> str:
    """
    Return the SHA-256 hash (hex) of given bytes.
    Useful for file integrity checks.
    """
    return hashlib.sha256(data).hexdigest()


def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    Read a text file safely and return its contents.
    """
    with open(path, "r", encoding=encoding, errors="ignore") as f:
        return f.read()


def write_file(path: str, text: str, encoding: str = "utf-8") -> None:
    """
    Write text to a file (overwrites by default).
    """
    with open(path, "w", encoding=encoding) as f:
        f.write(text)
