"""Androguard-based helpers for inspecting DEX bytecode.

This module extracts API call usage from an APK's DEX files and applies a
simple rule engine to highlight potentially risky patterns such as insecure
cryptography or unsafe WebView configuration.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    from androguard.misc import AnalyzeAPK  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    AnalyzeAPK = None  # type: ignore[assignment]

# Rule definitions map a simple name to substrings that should appear in the
# API call signature. The matching is intentionally coarse but provides a
# lightweight rule engine for common risky behaviours.
API_RULES: Dict[str, List[str]] = {
    # Use of outdated or insecure cryptographic primitives
    "insecure_crypto": [
        "Ljavax/crypto/Cipher;->getInstance",
        "Ljava/security/MessageDigest;->getInstance",
        "Ljavax/crypto/spec/DESKeySpec;-><init>",
    ],
    # WebView configurations that may expose JavaScript interfaces
    "webview": [
        "Landroid/webkit/WebView;->addJavascriptInterface",
        "Landroid/webkit/WebSettings;->setJavaScriptEnabled",
    ],
}


def extract_api_calls(apk_path: str) -> Dict[str, int]:
    """Return a mapping of API call signatures to occurrence counts.

    Parameters
    ----------
    apk_path:
        Path to the APK file to analyse.
    """

    if AnalyzeAPK is None:  # pragma: no cover - handled gracefully by caller
        raise RuntimeError("androguard is not installed")

    _apk, _d, dx = AnalyzeAPK(apk_path)  # type: ignore[misc]
    calls: Counter[str] = Counter()
    for method in dx.get_methods():
        for _caller, callee, _offset in method.get_xref_to():
            sig = f"{callee.class_name}->{callee.name}{callee.descriptor}"
            calls[sig] += 1
    return dict(calls)


def apply_rules(api_calls: Dict[str, int]) -> Dict[str, List[str]]:
    """Apply ``API_RULES`` to ``api_calls`` and return matches."""

    matches: Dict[str, List[str]] = {}
    for name, patterns in API_RULES.items():
        hits = [p for p in patterns if any(p in call for call in api_calls)]
        if hits:
            matches[name] = hits
    return matches


def summarize_apk(apk_path: str) -> Dict[str, Any]:
    """High level helper to return API usage and rule matches for ``apk_path``."""

    api_calls = extract_api_calls(apk_path)
    return {
        "api_calls": api_calls,
        "rule_matches": apply_rules(api_calls),
    }
