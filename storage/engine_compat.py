"""Compatibility wrapper for SQLAlchemy engine creation."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

logger = logging.getLogger(__name__)


def create_engine_safe(url: str, **kwargs: Any):
    """Create an engine, filtering unsupported pool args for SQLite.

    If ``pool_size`` or ``max_overflow`` are rejected by the backend or
    dialect, they are removed before retrying.  A debug message is logged when
    filtering occurs.
    """

    url_obj = make_url(url)
    filtered = dict(kwargs)
    removed: list[str] = []
    if url_obj.get_backend_name() == "sqlite":
        for key in ("pool_size", "max_overflow"):
            if key in filtered:
                removed.append(key)
                filtered.pop(key)
        if removed:
            logger.debug("create_engine_safe: filtered %s for sqlite", ", ".join(removed))
    try:
        return create_engine(url, **filtered)
    except TypeError:
        for key in ("pool_size", "max_overflow"):
            if key in filtered:
                removed.append(key)
                filtered.pop(key, None)
        if removed:
            logger.debug(
                "create_engine_safe: filtered %s after TypeError", ", ".join(sorted(set(removed)))
            )
            return create_engine(url, **filtered)
        raise
