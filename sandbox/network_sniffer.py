"""Network sniffer stub."""

from __future__ import annotations

from typing import List, Dict


def sniff_network(apk_path: str) -> List[Dict[str, str]]:
    """Return simulated network observations for the APK.

    Each entry contains a ``destination`` and ``protocol`` field.
    """
    return [{"destination": "example.com", "protocol": "TCP"}]
