# database/db_core.py
"""
Database core module (OO, connection-only).

Responsibilities in this module:
- Connection lifecycle management (single connection or pooled)
- Thread-safe access to connections
- Ping/health at the transport level (no SQL)
- Optional auto-reconnect policy
- A single facade (DatabaseCore) that other modules can depend on

Intentionally out of scope for this module:
- Creating cursors
- Executing queries
- Transactions and SQL helpers

Those concerns should live in a higher-level module such as database/db_engine.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterator
from contextlib import contextmanager
import threading
import time

import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool

# Import raw dict from your config; this keeps db_core unopinionated.
from database.db_config import DB_CONFIG


# -------------------------
# Data models
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
    # Reconnect policy for pings or stale connections in single-connection mode.
    reconnect_attempts: int = 2
    reconnect_backoff_sec: float = 0.3


# -------------------------
# Connection provider interface
# -------------------------

class ConnectionProvider:
    """
    Abstract base for connection providers.
    Implementations must NOT perform any SQL.
    """

    def connect(self) -> None:
        raise NotImplementedError

    def disconnect(self) -> None:
        raise NotImplementedError

    def is_ready(self) -> bool:
        raise NotImplementedError

    def ping(self, reconnect: bool = True) -> bool:
        raise NotImplementedError

    @contextmanager
    def connection(self) -> Iterator[MySQLConnection]:
        """
        Yield a live connection that the caller can use to create cursors.
        Implementations must NOT execute SQL here.
        """
        raise NotImplementedError


# -------------------------
# Single connection provider
# -------------------------

class SingleConnectionProvider(ConnectionProvider):
    """
    Manages one process-wide connection with optional auto-reconnect policy.
    Thread-safe. Does not execute SQL.
    """

    def __init__(
        self,
        settings: ConnectionSettings,
        options: RuntimeOptions,
    ) -> None:
        self._settings = settings
        self._options = options
        self._conn: Optional[MySQLConnection] = None
        self._lock = threading.RLock()

    def connect(self) -> None:
        with self._lock:
            if self._conn is None or not self._is_connected(self._conn):
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
        with self._lock:
            if self._conn is not None:
                try:
                    if self._is_connected(self._conn):
                        self._conn.close()
                finally:
                    self._conn = None

    def is_ready(self) -> bool:
        with self._lock:
            return self._conn is not None and self._is_connected(self._conn)

    def ping(self, reconnect: bool = True) -> bool:
        with self._lock:
            if self._conn is None:
                if reconnect:
                    return self._attempt_reconnect_locked()
                return False
            try:
                self._conn.ping(reconnect=reconnect, attempts=1, delay=0)
                return True
            except Error:
                if reconnect:
                    return self._attempt_reconnect_locked()
                return False

    @contextmanager
    def connection(self) -> Iterator[MySQLConnection]:
        """
        Yields the single managed connection. Ensures it is connected and pings it.
        """
        self.connect()
        # Optional ping to refresh TCP keepalive; does not run SQL.
        self.ping(reconnect=True)
        assert self._conn is not None
        yield self._conn

    # ---- internals ----

    def _attempt_reconnect_locked(self) -> bool:
        """
        Attempt to (re)connect using exponential backoff.
        Must be called with _lock held.
        """
        attempts = max(1, self._options.reconnect_attempts)
        delay = max(0.0, self._options.reconnect_backoff_sec)
        last_exc: Optional[Exception] = None

        for i in range(attempts):
            try:
                if self._conn is not None:
                    try:
                        self._conn.close()
                    except Exception:
                        pass
                self._conn = None
                self.connect()
                return True
            except Exception as exc:
                last_exc = exc
                time.sleep(delay * (2 ** i))
        if last_exc:
            # Swallowing the exception here keeps the provider SQL-free and side-effect minimal.
            # Caller can inspect is_ready() or the ping() boolean.
            pass
        return False

    @staticmethod
    def _is_connected(conn: Optional[MySQLConnection]) -> bool:
        try:
            return bool(conn) and conn.is_connected()
        except Exception:
            return False


# -------------------------
# Pooled connection provider
# -------------------------

class PooledConnectionProvider(ConnectionProvider):
    """
    Manages a pool of connections. Each context manager checkout yields
    a separate connection from the pool. Does not execute SQL.
    """

    def __init__(
        self,
        settings: ConnectionSettings,
        pool: PoolSettings,
        options: RuntimeOptions,
    ) -> None:
        self._settings = settings
        self._pool_cfg = pool
        self._options = options
        self._pool: Optional[MySQLConnectionPool] = None
        self._lock = threading.RLock()

    def connect(self) -> None:
        with self._lock:
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
        # mysql.connector pools do not expose an explicit close; connections
        # are closed when they are returned and GCed. We perform a light
        # best-effort drain by checking out and closing one.
        with self._lock:
            self._pool = None  # dropping reference allows cleanup by runtime

    def is_ready(self) -> bool:
        with self._lock:
            return self._pool is not None

    def ping(self, reconnect: bool = True) -> bool:
        """
        For a pool we test by checking out a connection and pinging it.
        """
        try:
            with self.connection() as conn:
                conn.ping(reconnect=reconnect, attempts=1, delay=0)
            return True
        except Error:
            if reconnect:
                # Rebuild the pool on failure
                with self._lock:
                    self._pool = None
                try:
                    self.connect()
                    with self.connection() as conn:
                        conn.ping(reconnect=True, attempts=1, delay=0)
                    return True
                except Exception:
                    return False
            return False

    @contextmanager
    def connection(self) -> Iterator[MySQLConnection]:
        self.connect()
        assert self._pool is not None
        conn = self._pool.get_connection()
        conn.autocommit = self._options.autocommit
        try:
            # Optional ping to refresh TCP keepalive; does not run SQL.
            try:
                conn.ping(reconnect=True, attempts=1, delay=0)
            except Error:
                # If this specific leased connection is bad, try once more.
                try:
                    conn.close()
                except Exception:
                    pass
                conn = self._pool.get_connection()
                conn.autocommit = self._options.autocommit
                conn.ping(reconnect=True, attempts=1, delay=0)
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass


# -------------------------
# Facade
# -------------------------

class DatabaseCore:
    """
    Facade that hides whether we are using a single connection or a pool.

    Other modules should depend on DatabaseCore or on the ConnectionProvider
    interface rather than on mysql.connector directly.
    """

    def __init__(
        self,
        provider: ConnectionProvider,
    ) -> None:
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
        """
        Build a DatabaseCore from DB_CONFIG or a provided mapping.
        """
        raw = dict(DB_CONFIG if cfg is None else cfg)
        settings = ConnectionSettings.from_mapping(raw)
        options = RuntimeOptions(
            autocommit=autocommit,
            reconnect_attempts=reconnect_attempts,
            reconnect_backoff_sec=reconnect_backoff_sec,
        )

        if use_pool:
            provider = PooledConnectionProvider(
                settings=settings,
                pool=PoolSettings(pool_name=pool_name, pool_size=pool_size),
                options=options,
            )
        else:
            provider = SingleConnectionProvider(
                settings=settings,
                options=options,
            )
        return DatabaseCore(provider)

    # Lifecycle

    def connect(self) -> None:
        self._provider.connect()

    def disconnect(self) -> None:
        self._provider.disconnect()

    def is_ready(self) -> bool:
        return self._provider.is_ready()

    def ping(self, reconnect: bool = True) -> bool:
        return self._provider.ping(reconnect=reconnect)

    # Connection context

    @contextmanager
    def connection(self) -> Iterator[MySQLConnection]:
        """
        Yield a live MySQLConnection to be used by higher-level code.
        No SQL is executed here.
        """
        with self._provider.connection() as conn:
            yield conn

    # Context manager sugar

    def __enter__(self) -> "DatabaseCore":
        """Connect on entry so ``with DatabaseCore(...)`` just works."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - thin wrapper
        self.disconnect()
        # Do not suppress exceptions
        return False
