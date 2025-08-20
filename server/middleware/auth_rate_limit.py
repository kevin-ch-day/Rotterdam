from __future__ import annotations

import hmac
import logging
import time
from collections import defaultdict, deque
from typing import Callable, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from . import config
from .config import MiddlewareSettings, settings

__all__ = [
    "AuthRateLimitMiddleware",
    "_request_log",
    "_last_cleanup",
    "_cleanup_request_log",
]

security_logger = logging.getLogger("rotterdam.security")

_request_log: dict[str, deque[float]] = defaultdict(
    lambda: deque(maxlen=4 * settings.rate_limit)
)
_last_cleanup: float = time.time()


def _cleanup_request_log(now: float, cfg: MiddlewareSettings = settings) -> None:
    """Remove empty or stale request log entries."""
    global _last_cleanup
    if now - _last_cleanup < cfg.rate_window_secs:
        return
    _last_cleanup = now
    stale: list[str] = []
    for bucket, window in list(_request_log.items()):
        if not window or (now - window[-1] >= cfg.rate_window_secs):
            stale.append(bucket)
    for bucket in stale:
        _request_log.pop(bucket, None)


def _is_public(path: str, cfg: MiddlewareSettings = settings) -> bool:
    if path in cfg.public_paths:
        return True
    return any(path.startswith(pfx) for pfx in cfg.public_prefixes)


def _extract_client_ip(
    request: Request, cfg: MiddlewareSettings = settings
) -> str:
    """Honor X-Forwarded-For when behind a trusted proxy (opt-in)."""
    if cfg.trust_proxy:
        xff = request.headers.get("x-forwarded-for")  # case-insensitive
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _dev_bypass(request: Request, cfg: MiddlewareSettings = settings) -> bool:
    if cfg.disable_auth:
        return True
    if cfg.trust_localhost:
        ip = _extract_client_ip(request, cfg)
        if ip in {"127.0.0.1", "::1"}:
            return True
    return False


def _get_presented_key(request: Request) -> str | None:
    """Read API key from X-API-Key or Authorization: Bearer <key>."""
    key = request.headers.get("X-API-Key")
    if key:
        return key.strip()
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    return None


def _constant_time_member(presented: str, valid_keys: Iterable[str]) -> bool:
    """Constant-time membership check over a small set of keys (no short-circuit)."""
    result = False
    for k in valid_keys:
        result = result or hmac.compare_digest(presented, k)
    return result


def _rate_limit_id(presented_key: str | None, request: Request) -> str:
    """Rate limit bucket identifier (prefer key, else IP)."""
    return presented_key or _extract_client_ip(request)


def _rate_limit_headers(limit: int, remaining: int, reset_in: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(remaining, 0)),
        "X-RateLimit-Reset": str(reset_in),
    }


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Validate an API key and apply naive per-minute rate limiting."""

    def __init__(
        self, app, settings: MiddlewareSettings | None = None
    ) -> None:
        super().__init__(app)
        self.settings = settings or config.settings

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        # 1) Always allow CORS preflight / OPTIONS
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # 2) Public routes & static assets
        cfg = self.settings

        if _is_public(path, cfg):
            return await call_next(request)

        # 3) Local/dev bypasses
        if _dev_bypass(request, cfg):
            return await call_next(request)

        # 4) Authenticate
        presented = _get_presented_key(request)
        if not presented or not _constant_time_member(presented, cfg.api_keys):
            client = _extract_client_ip(request, cfg)
            security_logger.warning("Unauthorized request from %s path=%s", client, path)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        # 5) Rate-limit (sliding window)
        bucket = _rate_limit_id(presented, request)
        now = time.time()
        _cleanup_request_log(now, cfg)
        window = _request_log[bucket]

        # prune entries outside window
        while window and now - window[0] >= cfg.rate_window_secs:
            window.popleft()

        if len(window) >= cfg.rate_limit:
            reset_in = max(0, int(cfg.rate_window_secs - (now - window[0])))
            security_logger.warning("Rate limit exceeded for %s path=%s", bucket, path)
            headers = _rate_limit_headers(cfg.rate_limit, 0, reset_in)
            # Optional: include Retry-After for clients that honor it
            headers.setdefault("Retry-After", str(reset_in))
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429, headers=headers)

        window.append(now)

        # 6) Call downstream
        response: Response = await call_next(request)

        # 7) Attach rate-limit headers
        remaining = cfg.rate_limit - len(window)
        reset_in = max(
            0,
            int(cfg.rate_window_secs - (now - window[0])) if window else cfg.rate_window_secs,
        )
        for k, v in _rate_limit_headers(cfg.rate_limit, remaining, reset_in).items():
            response.headers[k] = v

        return response
