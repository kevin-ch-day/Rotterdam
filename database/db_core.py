# database/db_core.py
"""
Simplified database core module.

- Supports single or pooled MySQL connections
- Provides connection lifecycle + ping
- Context manager for safe usage

Out of scope:
- Queries, cursors, transactions (live in db_engine.py)
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Iterator, Any

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

from database.db_config import DB_CONFIG


# -------------------------
# Single connection
# -------------------------

class SingleConnection:
    def __init__(self, cfg: dict, autocommit: bool = False) -> None:
        self._cfg = cfg
        self._conn: Optional[Any] = None
        self._autocommit = autocommit

    def connect(self) -> None:
        if not self._conn or not self.is_ready():
            conn = mysql.connector.connect(**self._cfg)
            conn.autocommit = self._autocommit  # type: ignore[attr-defined]
            self._conn = conn

    def disconnect(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def is_ready(self) -> bool:
        try:
            return bool(self._conn and self._conn.is_connected())
        except Exception:
            return False

    def ping(self) -> bool:
        try:
            if not self._conn:
                self.connect()
            if self._conn is not None:
                self._conn.ping(reconnect=True, attempts=1, delay=0)  # type: ignore[attr-defined]
            return True
        except Error:
            self.disconnect()
            return False

    @contextmanager
    def connection(self) -> Iterator[Any]:
        self.connect()
        self.ping()
        assert self._conn is not None
        yield self._conn


# -------------------------
# Connection pool
# -------------------------

class ConnectionPool:
    def __init__(self, cfg: dict, pool_name: str = "default_pool",
                 pool_size: int = 5, autocommit: bool = False) -> None:
        self._cfg = cfg
        self._pool_name = pool_name
        self._pool_size = pool_size
        self._pool: Optional[MySQLConnectionPool] = None
        self._autocommit = autocommit

    def connect(self) -> None:
        if self._pool is None:
            self._pool = MySQLConnectionPool(
                pool_name=self._pool_name,
                pool_size=self._pool_size,
                **self._cfg,
            )

    def disconnect(self) -> None:
        self._pool = None

    def is_ready(self) -> bool:
        return self._pool is not None

    def ping(self) -> bool:
        try:
            with self.connection() as conn:
                conn.ping(reconnect=True, attempts=1, delay=0)  # type: ignore[attr-defined]
            return True
        except Error:
            self.disconnect()
            return False

    @contextmanager
    def connection(self) -> Iterator[Any]:
        self.connect()
        assert self._pool is not None
        conn = self._pool.get_connection()
        conn.autocommit = self._autocommit  # type: ignore[attr-defined]
        try:
            conn.ping(reconnect=True, attempts=1, delay=0)  # type: ignore[attr-defined]
            yield conn
        finally:
            conn.close()


# -------------------------
# Facade
# -------------------------

class DatabaseCore:
    def __init__(self, provider: Any) -> None:
        self._provider = provider

    @staticmethod
    def from_config(use_pool: bool = False, **kwargs) -> "DatabaseCore":
        cfg = dict(DB_CONFIG)
        provider = (
            ConnectionPool(cfg, **kwargs)
            if use_pool else
            SingleConnection(cfg, **kwargs)
        )
        return DatabaseCore(provider)

    def connect(self) -> None:
        self._provider.connect()

    def disconnect(self) -> None:
        self._provider.disconnect()

    def ping(self) -> bool:
        return self._provider.ping()

    @contextmanager
    def connection(self) -> Iterator[Any]:
        with self._provider.connection() as conn:
            yield conn

    def __enter__(self) -> "DatabaseCore":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.disconnect()
        return False
