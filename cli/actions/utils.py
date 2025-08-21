from __future__ import annotations

from contextlib import contextmanager

from utils.logging_utils.app_logger import app_logger

logger = app_logger.get_logger(__name__)
log_context = app_logger.context


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
