# database/db_engine.py
"""
Simplified database engine module.

Responsibilities:
- Create cursors from DatabaseCore connections
- Execute SQL statements and queries
- Provide transaction and retry helpers

This layer does not know about domain models.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

from mysql.connector import Error, errorcode

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
        self._core = core
        self._default_dict_rows = default_dict_rows
        self._autocommit_writes = autocommit_writes

    # -------------------------
    # Lifecycle
    # -------------------------

    def init(self) -> None:
        self._core.connect()

    def shutdown(self) -> None:
        self._core.disconnect()

    def is_ready(self) -> bool:
        return self._core.ping()

    def __enter__(self) -> "DbEngine":
        self.init()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.shutdown()
        return False

    # -------------------------
    # Cursor + transactions
    # -------------------------

    @contextmanager
    def cursor(self, *, dict_rows: Optional[bool] = None) -> Iterator[Any]:
        dict_flag = self._default_dict_rows if dict_rows is None else dict_rows
        with self._core.connection() as conn:
            cur = conn.cursor(dictionary=dict_flag)  # type: ignore[arg-type]
            try:
                yield cur
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    @contextmanager
    def transaction(self, *, dict_rows: Optional[bool] = None) -> Iterator[Any]:
        dict_flag = self._default_dict_rows if dict_rows is None else dict_rows
        with self._core.connection() as conn:
            cur = conn.cursor(dictionary=dict_flag)  # type: ignore[arg-type]
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
    # Execution helpers
    # -------------------------

    def execute(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        commit: bool = False,
        dict_rows: Optional[bool] = None,
    ) -> int:
        with self._core.connection() as conn:
            cur = conn.cursor(dictionary=(self._default_dict_rows if dict_rows is None else dict_rows))  # type: ignore[arg-type]
            try:
                cur.execute(sql, params)
                affected = cur.rowcount
                if commit or (self._autocommit_writes and _is_write_statement(sql)):
                    conn.commit()
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
        with self._core.connection() as conn:
            cur = conn.cursor(dictionary=(self._default_dict_rows if dict_rows is None else dict_rows))  # type: ignore[arg-type]
            try:
                cur.executemany(sql, list(seq_of_params))
                affected = cur.rowcount
                if commit or (self._autocommit_writes and _is_write_statement(sql)):
                    conn.commit()
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
        with self.cursor(dict_rows=dict_rows) as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def fetch_val(self, sql: str, params: Optional[Params] = None) -> Optional[Any]:
        row = self.fetch_one(sql, params, dict_rows=False)
        if row is None:
            return None
        return row[0] if isinstance(row, (tuple, list)) else None

    # -------------------------
    # Utility helpers
    # -------------------------

    def table_exists(self, table_name: str) -> bool:
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
