# database/db_core.py
"""
Database core module (simplified).

Responsibilities:
- Connection lifecycle management (single or pooled)
- Ping/health checks (no SQL execution)
- Optional auto-reconnect policy
- Facade DatabaseCore class to hide backend details

Intentionally out of scope:
- Cursors
- Query execution
- Transactions

Those live in db_engine.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterator
from contextlib import contextmanager
import time

import mysql.connector
from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import MySQLConnectionPool

from database.db_config import DB_CONFIG


# -------------------------
# Config models
# -------------------------

@dataclass(frozen=True)
class ConnectionSettings:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    connection_timeout: int = 10

    @staticmethod
    def from_mapping(m: dict) -> "ConnectionSettings":
        return ConnectionSettings(
            host=m.get("host", "localhost"),
            user=m["user"],
            password=m.get("password", ""),
            database=m.get("database", ""),
            port=m.get("port", 3306),
            connection_timeout=m.get("connection_timeout", 10),
        )


@dataclass(frozen=True)
class PoolSettings:
    pool_name: str = "rotterdam_pool"
    pool_size: int = 5


@dataclass(frozen=True)
class RuntimeOptions:
    autocommit: bool = False
    reconnect_attempts: int = 2
    reconnect_backoff_sec: float = 0.3


# -------------------------
# Single connection provider
# -------------------------

class SingleConnectionProvider:
    def __init__(self, settings: ConnectionSettings, options: RuntimeOptions) -> None:
        self._settings = settings
        self._options = options
        self._conn: Optional[MySQLConnectionAbstract] = None

    def connect(self) -> None:
        if self._conn is None or not self.is_ready():
            self._conn = mysql.connector.connect(
                host=self._settings.host,
                user=self._settings.user,
                password=self._settings.password,
                database=self._settings.database,
                port=self._settings.port,
                connection_timeout=self._settings.connection_timeout,
            )
            self._conn.autocommit = self._options.autocommit

    def disconnect(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def is_ready(self) -> bool:
        return bool(self._conn and self._conn.is_connected())

    def ping(self) -> bool:
        try:
            if not self._conn:
                self.connect()
            self._conn.ping(reconnect=True, attempts=1, delay=0)
            return True
        except Error:
            return self._attempt_reconnect()

    @contextmanager
    def connection(self) -> Iterator[MySQLConnectionAbstract]:
        self.connect()
        self.ping()
        assert self._conn is not None
        yield self._conn

    def _attempt_reconnect(self) -> bool:
        for i in range(self._options.reconnect_attempts):
            try:
                time.sleep(self._options.reconnect_backoff_sec * (2 ** i))
                self.connect()
                return True
            except Exception:
                continue
        return False


# -------------------------
# Pooled connection provider
# -------------------------

class PooledConnectionProvider:
    def __init__(self, settings: ConnectionSettings, pool: PoolSettings, options: RuntimeOptions) -> None:
        self._settings = settings
        self._options = options
        self._pool_cfg = pool
        self._pool: Optional[MySQLConnectionPool] = None

    def connect(self) -> None:
        if self._pool is None:
            self._pool = MySQLConnectionPool(
                pool_name=self._pool_cfg.pool_name,
                pool_size=self._pool_cfg.pool_size,
                host=self._settings.host,
                user=self._settings.user,
                password=self._settings.password,
                database=self._settings.database,
                port=self._settings.port,
                connection_timeout=self._settings.connection_timeout,
            )

    def disconnect(self) -> None:
        self._pool = None  # GC cleans up connections

    def is_ready(self) -> bool:
        return self._pool is not None

    def ping(self) -> bool:
        try:
            with self.connection() as conn:
                conn.ping(reconnect=True, attempts=1, delay=0)
            return True
        except Error:
            self._pool = None
            return False

    @contextmanager
    def connection(self) -> Iterator[MySQLConnectionAbstract]:
        self.connect()
        assert self._pool is not None
        conn = self._pool.get_connection()
        conn.autocommit = self._options.autocommit
        try:
            conn.ping(reconnect=True, attempts=1, delay=0)
            yield conn
        finally:
            conn.close()


# -------------------------
# Facade
# -------------------------

class DatabaseCore:
    def __init__(self, provider) -> None:
        self._provider = provider

    @staticmethod
    def from_config(
        *,
        use_pool: bool = False,
        pool_name: str = "rotterdam_pool",
        pool_size: int = 5,
        autocommit: bool = False,
        reconnect_attempts: int = 2,
        reconnect_backoff_sec: float = 0.3,
        cfg: Optional[dict] = None,
    ) -> "DatabaseCore":
        raw = dict(DB_CONFIG if cfg is None else cfg)
        settings = ConnectionSettings.from_mapping(raw)
        options = RuntimeOptions(
            autocommit=autocommit,
            reconnect_attempts=reconnect_attempts,
            reconnect_backoff_sec=reconnect_backoff_sec,
        )
        provider = (
            PooledConnectionProvider(settings, PoolSettings(pool_name, pool_size), options)
            if use_pool
            else SingleConnectionProvider(settings, options)
        )
        return DatabaseCore(provider)

    def connect(self) -> None: self._provider.connect()
    def disconnect(self) -> None: self._provider.disconnect()
    def is_ready(self) -> bool: return self._provider.is_ready()
    def ping(self) -> bool: return self._provider.ping()

    @contextmanager
    def connection(self) -> Iterator[MySQLConnectionAbstract]:
        with self._provider.connection() as conn:
            yield conn

    def __enter__(self): self.connect(); return self
    def __exit__(self, exc_type, exc, tb): self.disconnect(); return False
