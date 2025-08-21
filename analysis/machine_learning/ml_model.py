# File: analysis/ml_model.py
"""Convenience wrapper for the Android static analysis ML model.

This module re-exports :func:`predict_malicious` so callers can simply
``from analysis.ml_model import predict_malicious`` without needing to know
the underlying package layout.  If the platform-specific implementation is
unavailable we raise a helpful runtime error when the function is invoked.
"""

from __future__ import annotations

try:  # pragma: no cover - defensive import
    from rotterdam.android.analysis.static.ml_model import predict_malicious
except Exception as exc:  # pragma: no cover - missing platform module
    def predict_malicious(*args: object, **kwargs: object):  # type: ignore[override]
        raise RuntimeError("ML model unavailable") from exc

__all__ = ["predict_malicious"]
