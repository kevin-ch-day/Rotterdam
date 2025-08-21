from __future__ import annotations

from contextlib import contextmanager
from typing import Any

# Optional logging integration
try:
    from logs.logging_config import StructuredLogger  # type: ignore

    logger = StructuredLogger.get_logger(__name__)  # type: ignore
    log_context = StructuredLogger.context  # type: ignore
except Exception:  # pragma: no cover
    import logging

    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    @contextmanager
    def log_context(**_: Any):  # type: ignore
        yield


@contextmanager
def action_context(
    action: str,
    *,
    device_serial: str | None = None,
    apk_path: str | None = None,
):
    """Wrapper around :func:`log_context` to reduce repetition in actions."""
    with log_context(action=action, device_serial=device_serial, apk_path=apk_path):
        yield
