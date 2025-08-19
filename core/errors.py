"""Utilities for consistent error handling across the application."""

from __future__ import annotations

from typing import Optional
import xml.etree.ElementTree as ET

from logging_config import get_logger

logger = get_logger(__name__)


def log_exception(message: str, exc: Exception) -> None:
    """Log an exception with a standard format."""
    logger.error("%s: %s", message, exc)


def safe_fromstring(xml_text: str, *, description: str = "XML") -> Optional[ET.Element]:
    """Safely parse XML text, returning ``None`` on failure.

    The caller is responsible for handling the ``None`` case.
    """
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log_exception(f"Failed to parse {description}", exc)
        return None
