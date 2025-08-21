# database/db_engine.py
"""
Database engine module.

Responsibilities:
- Create cursors from DatabaseCore connections
- Execute SQL statements and queries
- Provide transaction and retry helpers
- Keep all SQL concerns out of db_core

This layer does not know about domain models. Higher-level code can
import DbEngine and build repository-like modules on top of it.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from mysql.connector import Error, errorcode
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from database.db_core import DatabaseCore

Params = Union[Tuple[Any, ...], Dict[str, Any]]
T = TypeVar("T")


class DbEngine:
    def __init__(
        self,
        core: DatabaseCore,
        *,
        default_dict_rows: bool = False,
        autocommit_writes: bool = False,
    ) -> None:
        """
        Args:
            core: A DatabaseCore instance from db_core.
            default_dict_rows: Default cursor row format (dict vs tuple).
            autocommit_writes: If True, execute/ executemany will commit
                               automatically when not inside an explicit
                               transaction block. If False, callers should
                               either use transaction() or pass commit=True.
        """
        self._core = core
        self._default_dict_rows = default_dict_rows
        self._autocommit_writes = autocommit_writes

    # -------------------------
    # Lifecycle passthroughs
    # -------------------------

    def init(self) -> None:
        self._core.connect()

    def shutdown(self) -> None:
        self._core.disconnect()

    def is_ready(self) -> bool:
        return self._core.is_ready()

    def ping(self, reconnect: bool = True) -> bool:
        return self._core.ping(reconnect=reconnect)

    # -------------------------
    # Cursor and transaction contexts
    # -------------------------

    @contextmanager
    def cursor(self, *, dict_rows: Optional[bool] = None) -> Iterator[MySQLCursor]:
        """
        Context manager yielding a raw cursor.
        Use this for simple one-off statements when you want full control.
        """
        dict_flag = self._default_dict_rows if dict_rows is None else dict_rows
        with self._core.connection() as conn:
            cur = conn.cursor(dictionary=dict_flag)
            try:
                yield cur
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    @contextmanager
    def transaction(self, *, dict_rows: Optional[bool] = None) -> Iterator[MySQLCursor]:
        """
        Transaction context manager.
        Commits on success, rolls back on exception.
        """
        with self._core.connection() as conn:
            cur = conn.cursor(
                dictionary=(self._default_dict_rows if dict_rows is None else dict_rows)
            )
            try:
                yield cur
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    # -------------------------
    # Execution helpers (no domain logic)
    # -------------------------

    def execute(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        commit: bool = False,
        dict_rows: Optional[bool] = None,
    ) -> int:
        """
        Execute a single SQL statement. Returns rowcount.
        If commit is True, commits after execution.
        If autocommit_writes is True and commit is False, performs a commit
        only for data-changing statements when outside a transaction context.
        """
        with self._core.connection() as conn:
            cur = conn.cursor(
                dictionary=(self._default_dict_rows if dict_rows is None else dict_rows)
            )
            try:
                cur.execute(sql, params)
                affected = cur.rowcount
                if commit or (self._autocommit_writes and _is_write_statement(sql)):
                    try:
                        conn.commit()
                    except Exception:
                        pass
                return affected
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    def executemany(
        self,
        sql: str,
        seq_of_params: Iterable[Params],
        *,
        commit: bool = False,
        dict_rows: Optional[bool] = None,
    ) -> int:
        """
        Execute a statement for multiple parameter sets. Returns rowcount.
        """
        with self._core.connection() as conn:
            cur = conn.cursor(
                dictionary=(self._default_dict_rows if dict_rows is None else dict_rows)
            )
            try:
                cur.executemany(sql, list(seq_of_params))
                affected = cur.rowcount
                if commit or (self._autocommit_writes and _is_write_statement(sql)):
                    try:
                        conn.commit()
                    except Exception:
                        pass
                return affected
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    def fetch_one(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        dict_rows: Optional[bool] = None,
    ) -> Optional[Union[Tuple[Any, ...], Dict[str, Any]]]:
        """
        Execute a SELECT and fetch a single row. Returns None if no rows.
        """
        with self.cursor(dict_rows=dict_rows) as cur:
            cur.execute(sql, params)
            return cur.fetchone()

    def fetch_all(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        dict_rows: Optional[bool] = None,
    ) -> List[Union[Tuple[Any, ...], Dict[str, Any]]]:
        """
        Execute a SELECT and fetch all rows.
        """
        with self.cursor(dict_rows=dict_rows) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def fetch_val(
        self,
        sql: str,
        params: Optional[Params] = None,
    ) -> Optional[Any]:
        """
        Execute a SELECT that returns a single scalar value.
        Returns None if there is no row.
        """
        row = self.fetch_one(sql, params, dict_rows=False)
        if row is None:
            return None
        # row is a tuple in dict_rows=False mode
        return row[0] if isinstance(row, (tuple, list)) else None

    # -------------------------
    # Utility helpers
    # -------------------------

    def table_exists(self, table_name: str) -> bool:
        """
        Lightweight helper that checks if a table exists in the current schema.
        Uses SHOW TABLES LIKE to avoid touching information_schema unnecessarily.
        """
        row = self.fetch_one("SHOW TABLES LIKE %s", (table_name,), dict_rows=False)
        return row is not None

    def with_retry(
        self,
        fn: Callable[[], T],
        *,
        max_attempts: int = 3,
        backoff_sec: float = 0.25,
        transient_only: bool = True,
    ) -> T:
        """
        Run a callable with simple retry for transient MySQL errors.

        Args:
            fn: Zero-argument callable to execute.
            max_attempts: Maximum number of attempts before failing.
            backoff_sec: Initial backoff time between attempts.
            transient_only: If True only retry known transient MySQL errors.

        Returns:
            The value returned by ``fn`` on success.

        Raises:
            Exception: The last captured exception after exhausting retries.
        """

        attempt = 0
        last_exc: Optional[Exception] = None
        transient_codes = {
            errorcode.CR_SERVER_LOST,
            errorcode.CR_SERVER_GONE_ERROR,
            errorcode.ER_LOCK_DEADLOCK,
            errorcode.ER_LOCK_WAIT_TIMEOUT,
        }

        while attempt < max_attempts:
            try:
                return fn()
            except Error as e:
                last_exc = e
                if transient_only and getattr(e, "errno", None) not in transient_codes:
                    break
            except Exception as e:
                last_exc = e
                break

            time.sleep(backoff_sec * (2**attempt))
            attempt += 1

        if last_exc is not None:
            raise last_exc

        raise RuntimeError("with_retry: function did not return a value")


# -------------------------
# Internal helpers
# -------------------------

_WRITE_PREFIXES = (
    "insert",
    "update",
    "delete",
    "replace",
    "create",
    "alter",
    "drop",
    "truncate",
    "rename",
    "grant",
    "revoke",
)


def _is_write_statement(sql: str) -> bool:
    s = sql.lstrip().lower()
    return s.startswith(_WRITE_PREFIXES)
