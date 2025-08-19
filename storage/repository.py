from __future__ import annotations

"""Database engine and session helpers for MySQL storage.

The database configuration is loaded from a ``.env`` file located at the
project root. ``DATABASE_URL`` must be provided in this file or as an
environment variable. A minimal ``.env`` parser is included below.

Default fallback (for dev/tests):
    mysql+mysqlconnector://rotterdam_user:ChangeMe@127.0.0.1:3306/rotterdam
"""

import contextlib
import os
from pathlib import Path
import time
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _load_database_url() -> str:
    """Load ``DATABASE_URL`` from environment or ``.env`` file.

    If no value is found, a development default is returned so that imports
    do not fail during testing. The default uses the mysql-connector driver.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
            url = os.getenv("DATABASE_URL")

    if not url:
        url = "mysql+mysqlconnector://rotterdam_user:ChangeMe@127.0.0.1:3306/rotterdam"
    return url


# Cached DSN for reuse by downstream modules
DATABASE_URL = _load_database_url()

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy Engine."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
            echo=False,
            future=True,
            # mysql-connector-python supports this; harmless for others using this DSN.
            connect_args={"connection_timeout": 3},
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _engine


def get_session() -> Session:
    """Return a new Session bound to the singleton engine."""
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal()  # type: ignore[operator]


@contextlib.contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping_db() -> tuple[bool, str, float]:
    """Ping the DB and return (ok, version_or_error, latency_ms)."""
    eng = get_engine()
    t0 = time.perf_counter()
    try:
        with eng.connect() as conn:
            ver = conn.execute(text("SELECT VERSION()")).scalar() or "unknown"
        ms = (time.perf_counter() - t0) * 1000.0
        return True, str(ver), ms
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000.0
        return False, f"{e.__class__.__name__}: {e}", ms
