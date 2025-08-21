#!/usr/bin/env python3
# File: utils/display_utils/table.py
# table.py
"""
Table display utilities for Rotterdam.
Pure ASCII table rendering with width handling and safe truncation.
"""

from __future__ import annotations

import shutil
from typing import Any, Iterable, List, Optional, Sequence


def term_width(default: int = 80) -> int:
    """Best-effort terminal width."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default


def _stringify(row: Sequence[Any]) -> List[str]:
    return ["" if (c is None) else str(c) for c in row]


def _compute_widths(
    rows: List[List[str]], headers: Optional[Sequence[str]], max_total: int
) -> List[int]:
    all_rows = []
    if headers:
        all_rows.append(list(headers))
    all_rows += rows

    col_count = max((len(r) for r in all_rows), default=0)
    widths = [0] * col_count

    for r in all_rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    sep_space = 3 * (col_count - 1) if col_count > 0 else 0
    total = sum(widths) + sep_space

    if total <= max_total:
        return widths

    # shrink loop
    over = total - max_total
    MIN_W = 6
    while over > 0:
        idx = max(range(col_count), key=lambda i: widths[i])
        if widths[idx] <= MIN_W:
            reducible = [i for i, w in enumerate(widths) if w > MIN_W]
            if not reducible:
                break
            idx = max(reducible, key=lambda i: widths[i])
        widths[idx] -= 1
        over -= 1
    return widths


def _truncate(cell: str, width: int) -> str:
    if len(cell) <= width:
        return cell
    if width <= 3:
        return cell[:width]
    return cell[: width - 1 - 2] + "…"


def print_table(
    rows: Iterable[Sequence[Any]],
    headers: Optional[Sequence[str]] = None,
    max_width: Optional[int] = None,
) -> None:
    """
    Render a simple ASCII table.
    - rows: iterable of sequences
    - headers: optional sequence of column headers
    - max_width: clamp table to terminal width (default: terminal width)
    """
    string_rows: List[List[str]] = [_stringify(r) for r in rows]
    max_w = max_width or term_width()
    widths = _compute_widths(string_rows, headers, max_w)

    def fmt_row(row: Sequence[str]) -> str:
        cells = []
        for i, cell in enumerate(row):
            w = widths[i] if i < len(widths) else 8
            cells.append(f"{_truncate(cell, w):<{w}}")
        return " | ".join(cells)

    if headers:
        print(fmt_row(list(headers)))
        print("-" * min(sum(widths) + 3 * (len(widths) - 1), max_w))

    for r in string_rows:
        print(fmt_row(r))
