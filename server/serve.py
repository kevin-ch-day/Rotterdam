# server/serve.py
from __future__ import annotations

import logging
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import uvicorn

from settings import get_settings

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _wait_for_port(host: str, port: int, timeout: float = 5.0) -> bool:
    """Return True once TCP connect succeeds before timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _open_browser_later(host: str, port: int, timeout: float = 3.0) -> None:
    """Background helper: open browser when the server socket is listening."""
    if _wait_for_port(host, port, timeout=timeout):
        try:
            webbrowser.open(f"http://{host}:{port}/")
        except Exception:
            pass


def _validate_host_port(host: str, port: int) -> None:
    if not (1 <= port <= 65535):
        raise ValueError(f"Invalid port: {port} (must be 1–65535)")
    # Quick host sanity; allow IPv6/hostnames too, so keep it light.
    if not host:
        raise ValueError("Host cannot be empty")


def serve(
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    reload: Optional[bool] = None,
    workers: Optional[int] = None,
    open_browser: Optional[bool] = None,
) -> None:
    """
    Start the FastAPI app (server.main:app) via uvicorn with validated settings.

    Usage (from menu option [5]):
        from server.serve import serve
        serve()  # uses settings.get_settings() (env overrides honored)

    You can also override per-call:
        serve(port=8765, reload=True, open_browser=False)
    """
    s = get_settings()
    # Merge call-time overrides with centralized config
    h = s.host if host is None else host
    p = s.port if port is None else int(port)
    lvl = s.log_level if log_level is None else str(log_level).lower()
    ob = s.open_browser if open_browser is None else bool(open_browser)

    # Reload/worker defaults (safe for dev)
    use_reload = bool(reload) if reload is not None else False
    use_workers = int(workers) if workers is not None else 1
    if use_reload and use_workers != 1:
        # Uvicorn doesn't support reload with workers>1; normalize safely.
        use_workers = 1

    _validate_host_port(h, p)

    config = uvicorn.Config(
        "server.main:app",
        host=h,
        port=p,
        log_level=lvl,
        reload=use_reload,
        workers=use_workers,
    )
    server = uvicorn.Server(config)

    if ob:
        t = threading.Thread(target=_open_browser_later, args=(h, p), daemon=True)
        t.start()

    server.run()
