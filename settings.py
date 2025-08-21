from __future__ import annotations

import os
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
def get_settings() -> Settings:
    return Settings(
        host=os.getenv("APP_HOST", legacy.DEFAULT_HOST),
        port=int(os.getenv("APP_PORT", legacy.DEFAULT_PORT)),
        log_level=os.getenv("UVICORN_LOG_LEVEL", legacy.DEFAULT_LOG_LEVEL),
        open_browser=os.getenv("OPEN_BROWSER", "true").lower() not in {"false", "0", "no"},
    )
