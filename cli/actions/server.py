from __future__ import annotations

import socket
import threading
import webbrowser

from server.serve import serve
from settings import get_settings
from utils.display_utils import display

from .utils import action_context as _action_context
from .utils import logger


def show_database_status() -> None:
    """Indicate that the persistent database layer is disabled."""
    logger.info("show_database_status")
    display.print_section("Database")
    print("Database functionality is currently disabled in the CLI-focused MVP.")


def launch_web_app(host: str = get_settings().host, port: int = get_settings().port) -> None:
    """Launch the web interface, starting the server if needed."""
    logger.info("launch_web_app", extra={"host": host, "port": port})

    def _port_open() -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((host, port))
                return True
            except OSError:
                return False

    if not _port_open():
        threading.Thread(
            target=serve,
            kwargs={"host": host, "port": port, "open_browser": True},
            daemon=True,
        ).start()
    else:
        webbrowser.open(f"http://{host}:{port}")


def run_server(host: str = get_settings().host, port: int = get_settings().port) -> None:
    """Start the API server using centralized config."""
    with _action_context("run_server"):
        serve(host=host, port=port, open_browser=False)
