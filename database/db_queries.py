"""
Common SQL helpers built on top of :mod:`database.db_engine`.

These are small wrappers around :class:`DbEngine` for common inspection
queries during development or debugging. They intentionally avoid
domain-specific logic so they remain reusable across projects.
"""

from __future__ import annotations
from typing import List, Optional

from database.db_engine import DbEngine


def fetch_version(engine: DbEngine) -> Optional[str]:
    """Return the database server version string."""
    row = engine.fetch_one("SELECT VERSION() AS version", dict_rows=True)
    if isinstance(row, dict):
        return row.get("version")
    return None


def list_tables(engine: DbEngine) -> List[str]:
    """Return the list of tables in the current database schema."""
    rows = engine.fetch_all("SHOW TABLES", dict_rows=False)
    # rows is a list of single-element tuples -> unpack them safely
    return [name for (name,) in rows if name]


def table_exists(engine: DbEngine, table_name: str) -> bool:
    """Check if a table exists in the current schema."""
    row = engine.fetch_one("SHOW TABLES LIKE %s", (table_name,), dict_rows=False)
    return row is not None


def count_rows(engine: DbEngine, table_name: str) -> int:
    """Return the number of rows in the given table."""
    row = engine.fetch_val(f"SELECT COUNT(*) FROM `{table_name}`")
    return int(row) if row is not None else 0


__all__ = ["fetch_version", "list_tables", "table_exists", "count_rows"]
