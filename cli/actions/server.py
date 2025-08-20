from __future__ import annotations

import socket
import threading
import time
import webbrowser

from sqlalchemy import text

from core import display
from storage.repository import (
    AnalysisRepository,
    session_scope,
    DATABASE_URL,
    ping_db,
)

from .utils import action_context as _action_context, logger


def _fetch_recent_analyses(conn, limit: int = 10) -> list[list[str | int | None]]:
    """Return the most recent analyses records for display."""
    try:
        res = conn.execute(
            text(
                "SELECT package_name, score, status "
                "FROM analyses ORDER BY id DESC LIMIT :lim"
            ),
            {"lim": limit},
        )
        return [[row[0], row[1], row[2]] for row in res]
    except Exception:
        return []


def _redact(url: str) -> str:
    """Hide password in DSN when printing."""
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest and ":" in rest.split("@", 1)[0]:
        creds, hostpart = rest.split("@", 1)
        user = creds.split(":", 1)[0]
        rest = f"{user}:***@{hostpart}"
    return f"{scheme}://{rest}"


def show_database_status() -> None:
    """Report connectivity and basic statistics for the configured database."""
    logger.info("show_database_status")

    display.print_section("Database")
    print(f"DSN: {_redact(DATABASE_URL)}")

    ok, ver_or_err, ms = ping_db()
    if ok:
        display.good(f"MySQL version: {ver_or_err} ({ms:.1f} ms)")
    else:
        display.warn(f"DB check failed in {ms:.1f} ms → {ver_or_err}")
        return

    try:
        with session_scope() as s:
            rows = _fetch_recent_analyses(s, limit=10)  # type: ignore[arg-type]
    except Exception:
        rows = []

    display.print_section("Recent Analyses")
    if rows:
        display.print_table(rows, headers=["Package", "Score", "Status"])
    else:
        print("No analysis records found.")


def launch_web_app(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the web interface, starting the server if needed."""
    import uvicorn

    logger.info("launch_web_app", extra={"host": host, "port": port})

    def _port_open() -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((host, port))
                return True
            except OSError:
                return False

    if not _port_open():
        thread = threading.Thread(
            target=uvicorn.run,
            args=("server:app",),
            kwargs={"host": host, "port": port},
            daemon=True,
        )
        thread.start()
        time.sleep(0.5)

    webbrowser.open(f"http://{host}:{port}")


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the API server using uvicorn."""
    import uvicorn

    with _action_context("run_server"):
        uvicorn.run("server:app", host=host, port=port)

