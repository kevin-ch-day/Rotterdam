from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
import logging
import shutil
import socket

from server import serv_config as legacy


@dataclass
class Settings:
    host: str = legacy.DEFAULT_HOST
    port: int = legacy.DEFAULT_PORT
    log_level: str = legacy.DEFAULT_LOG_LEVEL
    open_browser: bool = True
    adb_bin: str = "adb"


@lru_cache()
def get_settings() -> Settings:
    """Return application settings with environment overrides."""

    logger = logging.getLogger("settings")

    # Host validation
    env_host = os.getenv("APP_HOST", legacy.DEFAULT_HOST).strip()
    host = env_host or legacy.DEFAULT_HOST
    if not env_host:
        logger.warning("APP_HOST empty; using %s", legacy.DEFAULT_HOST)
    else:
        try:
            socket.getaddrinfo(env_host, None)
        except Exception:
            logger.warning("Invalid APP_HOST %r; using %s", env_host, legacy.DEFAULT_HOST)
            host = legacy.DEFAULT_HOST

    # Port validation (use default on failure)
    raw_port = os.getenv("APP_PORT", str(legacy.DEFAULT_PORT))
    try:
        port = int(raw_port)
        if not (1024 <= port <= 65535):
            raise ValueError
    except ValueError:
        logger.warning("APP_PORT %r invalid; using %s", raw_port, legacy.DEFAULT_PORT)
        port = legacy.DEFAULT_PORT

    log_level = os.getenv("UVICORN_LOG_LEVEL", legacy.DEFAULT_LOG_LEVEL)

    # Browser gating
    truthy = {"1", "true", "yes", "on"}
    open_browser = os.getenv("OPEN_BROWSER", "true").strip().lower() in truthy
    if open_browser:
        if host not in {"127.0.0.1", "localhost", "::1"}:
            logger.info("OPEN_BROWSER disabled: non-loopback host %s", host)
            open_browser = False
        elif not os.getenv("DISPLAY"):
            logger.info("OPEN_BROWSER disabled: no DISPLAY detected")
            open_browser = False

    # ADB path resolution
    adb_env = os.getenv("ADB")
    if adb_env and os.access(adb_env, os.X_OK):
        adb_bin = adb_env
    else:
        fedora_default = os.path.expanduser("~/Android/Sdk/platform-tools/adb")
        if os.access(fedora_default, os.X_OK):
            adb_bin = fedora_default
        else:
            adb_bin = shutil.which("adb") or adb_env or fedora_default or "adb"

    return Settings(
        host=host,
        port=port,
        log_level=log_level,
        open_browser=open_browser,
        adb_bin=adb_bin,
    )
