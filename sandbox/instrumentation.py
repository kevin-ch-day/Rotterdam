"""Frida instrumentation management utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, List


class FridaInstrumentation:
    """Load Frida scripts and simulate a session lifecycle.

    The real project would use :mod:`frida` to attach to the target process and
    inject JavaScript hooks.  For testing purposes we provide a lightweight
    stand-in that simply reads the requested hook templates from disk and
    produces deterministic events when the session is active.
    """

    def __init__(self, scripts: Iterable[str], scripts_dir: Path | None = None) -> None:
        self.scripts = list(scripts)
        self.scripts_dir = scripts_dir or Path(__file__).with_name("frida_scripts")
        self.loaded_scripts: Dict[str, str] = {}
        self._active = False
        self._events: List[str] = []

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def load_scripts(self) -> None:
        """Load all requested scripts from :attr:`scripts_dir`."""
        for name in self.scripts:
            path = self.scripts_dir / f"{name}.js"
            self.loaded_scripts[name] = path.read_text(encoding="utf-8")

    def __enter__(self) -> "FridaInstrumentation":
        self.load_scripts()
        self._active = True
        # Generate deterministic example events for tests.
        if "http_logger" in self.loaded_scripts:
            self._events.append("NETWORK:http://example.com")
        if "crypto_usage" in self.loaded_scripts:
            self._events.append("PERMISSION:android.permission.CRYPTO")
            self._events.append("FILE_WRITE:/data/data/app/keystore.db")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - standard CM signature
        self._active = False

    # ------------------------------------------------------------------
    # Event streaming
    # ------------------------------------------------------------------
    def stream_events(self) -> Iterator[str]:
        """Yield instrumentation events captured during the session."""
        if not self._active:
            return
        for event in self._events:
            yield event
