# database/db_config.py
"""Database configuration constants used by :mod:`database`.

The values are intentionally hard coded for a local development database. In a
real application these would likely be loaded from environment variables or a
configuration file, but keeping them inline makes the examples in this
repository self‑contained and easy to understand.
"""

from typing import Final, Dict


DB_CONFIG: Final[Dict[str, object]] = {
    "host": "localhost",
    "user": "root",
    "password": "NewStrongPass!",
    "database": "mydatabase",
    # Optional extras used by :func:`DatabaseCore.from_config`
    "port": 3306,
    "connection_timeout": 10,
}

__all__ = ["DB_CONFIG"]
