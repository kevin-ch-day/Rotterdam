"""Common SQL helpers built on top of :mod:`database.db_engine`.

This module exposes tiny wrappers around :class:`DbEngine` for queries that
are handy during development or debugging. They avoid domain specific logic so
that the helpers remain reusable across projects.
"""

from __future__ import annotations

from typing import List, Optional

from database.db_engine import DbEngine


def fetch_version(engine: DbEngine) -> Optional[str]:
    """Return the database server version string.

    Args:
        engine: The :class:`DbEngine` instance to use.

    Returns:
        The version string if available, otherwise ``None``.
    """

    row = engine.fetch_one("SELECT VERSION() AS version", dict_rows=True)
    return row.get("version") if row else None


def list_tables(engine: DbEngine) -> List[str]:
    """Return the list of tables in the current database schema."""

    rows = engine.fetch_all("SHOW TABLES", dict_rows=False)
    return [r[0] for r in rows]


__all__ = ["fetch_version", "list_tables"]
