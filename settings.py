from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from functools import lru_cache

from server import serv_config as legacy


@dataclass
class Settings:
    host: str = legacy.DEFAULT_HOST
    port: int = legacy.DEFAULT_PORT
    log_level: str = legacy.DEFAULT_LOG_LEVEL
    open_browser: bool = True


@lru_cache()
def _env(new: str, old: str, default: str) -> str:
    if (val := os.getenv(new)) is not None:
        return val
    if (val := os.getenv(old)) is not None:
        warnings.warn(f"{old} is deprecated; use {new}", DeprecationWarning, stacklevel=2)
        return val
    return default


def get_settings() -> Settings:
    return Settings(
        host=_env("ROTTERDAM_APP_HOST", "APP_HOST", legacy.DEFAULT_HOST),
        port=int(_env("ROTTERDAM_APP_PORT", "APP_PORT", str(legacy.DEFAULT_PORT))),
        log_level=os.getenv("UVICORN_LOG_LEVEL", legacy.DEFAULT_LOG_LEVEL),
        open_browser=os.getenv("OPEN_BROWSER", "true").lower() not in {"false", "0", "no"},
    )
