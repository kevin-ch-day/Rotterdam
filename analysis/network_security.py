"""Utilities for parsing Android network security configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from core.errors import safe_fromstring

ANDROID_NS = "http://schemas.android.com/apk/res/android"


def locate_config(base: Path) -> Optional[Path]:
    """Return the first ``network_security_config.xml`` under ``base`` if present."""
    try:
        return next(base.rglob("network_security_config.xml"))
    except StopIteration:
        return None


def parse_network_security_config(xml_text: str) -> Dict[str, bool]:
    """Extract cleartext allowances, certificate pinning and debug overrides."""
    root = safe_fromstring(xml_text, description="network security config")
    if root is None:
        return {}

    ns = f"{{{ANDROID_NS}}}"
    cleartext = False
    pinning = False
    debug_overrides = root.find("debug-overrides") is not None

    base_cfg = root.find("base-config")
    if base_cfg is not None:
        if base_cfg.get(f"{ns}cleartextTrafficPermitted") == "true":
            cleartext = True
        if base_cfg.find("pin-set") is not None:
            pinning = True

    for domain_cfg in root.findall("domain-config"):
        if domain_cfg.get(f"{ns}cleartextTrafficPermitted") == "true":
            cleartext = True
        if domain_cfg.find("pin-set") is not None:
            pinning = True

    return {
        "cleartext_permitted": cleartext,
        "certificate_pinning": pinning,
        "debug_overrides": debug_overrides,
    }


def extract_network_security(base: Path) -> Dict[str, bool]:
    """Locate and parse a ``network_security_config.xml`` under ``base``."""
    cfg = locate_config(base)
    if cfg is None:
        return {}
    try:
        text = cfg.read_text()
    except OSError:
        return {}
    return parse_network_security_config(text)
