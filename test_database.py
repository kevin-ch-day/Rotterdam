"""Simple script to exercise the database layer.

Run ``python test_database.py`` to attempt a connection using the settings in
``database/db_config.py``. The script prints the database version and the list
of available tables if a connection can be established.
"""

from __future__ import annotations

import sys

# Ensure stdlib modules take precedence over same-named local packages (e.g., "platform")
sys.path.append(sys.path.pop(0))

from mysql.connector import Error

from database import db_queries
from database.db_core import DatabaseCore
from database.db_engine import DbEngine


def main() -> None:
    core = DatabaseCore.from_config()
    engine = DbEngine(core, default_dict_rows=True)

    try:
        engine.init()
    except Error as exc:  # pragma: no cover - diagnostic script
        print(f"Failed to connect: {exc}")
        return

    try:
        if not engine.ping():
            print("Database ping failed")
            return

        version = db_queries.fetch_version(engine)
        print(f"Database version: {version}")

        tables = db_queries.list_tables(engine)
        print(f"Tables ({len(tables)}): {tables}")
    finally:
        engine.shutdown()


if __name__ == "__main__":  # pragma: no cover - diagnostic script
    main()
