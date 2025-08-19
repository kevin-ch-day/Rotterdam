"""Runtime permission monitor stub."""

from __future__ import annotations

from typing import List


def collect_permissions(apk_path: str) -> List[str]:
    """Return a list of runtime permissions observed for the APK.

    This implementation is a stub that returns a canned list of
    permissions for demonstration and testing purposes.
    """
    return ["android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"]
