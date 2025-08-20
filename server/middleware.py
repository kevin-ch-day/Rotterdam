"""Authentication, rate limiting and request ID middleware."""

from __future__ import annotations

import contextvars
import hmac
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from typing import Callable, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

# -----------------------------------------------------------------------------
# Config (robust env parsing)
# -----------------------------------------------------------------------------

def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default

# Comma-separated list of valid API keys. Default "secret" (development only).
DEFAULT_API_KEY = "secret"
_API_KEYS_ENV = os.getenv("ROTTERDAM_API_KEY", DEFAULT_API_KEY)
API_KEYS: set[str] = {k.strip() for k in _API_KEYS_ENV.split(",") if k.strip()}

# Allow up to N requests per minute per client (IP or token).
RATE_LIMIT = max(1, _env_int("ROTTERDAM_RATE_LIMIT", 60))
RATE_WINDOW_SECS = max(1, _env_int("ROTTERDAM_RATE_WINDOW_SECS", 60))

# Dev/ops flags
DISABLE_AUTH = _env_bool("DISABLE_AUTH", False)
TRUST_LOCALHOST = _env_bool("TRUST_LOCALHOST", False)
TRUST_PROXY = _env_bool("TRUST_PROXY", False)

# Public routes (no auth). We intentionally EXCLUDE "/_diag" (requires auth or dev flag).
# Include the mount roots themselves so "/ui" (no trailing slash) works, too.
PUBLIC_PATHS: set[str] = {
    "/",
    "/favicon.ico",
    "/_healthz",
    "/_ready",
    "/ui",
    "/static",
    "/css",
    "/js",
    "/images",
    "/img",
    "/fonts",
}
PUBLIC_PREFIXES: tuple[str, ...] = (
    "/ui/",
    "/static/",
    "/css/",
    "/js/",
    "/images/",
    "/img/",
    "/fonts/",
)

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------

# Sliding window per client key — use deque for efficient pops from left.
# Keyed by client identifier (API key if present, else client IP).
_request_log: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=4 * RATE_LIMIT))
_last_cleanup: float = time.time()

def _cleanup_request_log(now: float) -> None:
    """Remove empty or stale request log entries."""
    global _last_cleanup
    if now - _last_cleanup < RATE_WINDOW_SECS:
        return
    _last_cleanup = now
    stale: list[str] = []
    for bucket, window in list(_request_log.items()):
        if not window or (now - window[-1] >= RATE_WINDOW_SECS):
            stale.append(bucket)
    for bucket in stale:
        _request_log.pop(bucket, None)

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

security_logger = logging.getLogger("rotterdam.security")
request_logger = logging.getLogger("rotterdam.request")

# Warn loudly if someone forgot to change the default key and didn’t disable auth
if DEFAULT_API_KEY in API_KEYS and not DISABLE_AUTH:
    logging.getLogger("uvicorn.error").critical(
        "ROTTERDAM_API_KEY is using the default value; set a custom key for production"
    )

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def get_request_id() -> str | None:
    """Return the request ID for the current context."""
    return _request_id_ctx.get()

def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(pfx) for pfx in PUBLIC_PREFIXES)

def _extract_client_ip(request: Request) -> str:
    """Honor X-Forwarded-For when behind a trusted proxy (opt-in)."""
    if TRUST_PROXY:
        xff = request.headers.get("x-forwarded-for")  # case-insensitive
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def _dev_bypass(request: Request) -> bool:
    if DISABLE_AUTH:
        return True
    if TRUST_LOCALHOST:
        ip = _extract_client_ip(request)
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

# -----------------------------------------------------------------------------
# Middlewares
# -----------------------------------------------------------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next: Callable):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        _request_id_ctx.set(req_id)
        try:
            response: Response = await call_next(request)
        except Exception:
            # Ensure we always return a response with the request ID on errors
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
            response.headers["X-Request-ID"] = req_id
            request_logger.exception("%s %s - id=%s", request.method, request.url.path, req_id)
            return response
        response.headers["X-Request-ID"] = req_id
        request_logger.info("%s %s - id=%s", request.method, request.url.path, req_id)
        return response

class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Validate an API key and apply naive per-minute rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        # 1) Always allow CORS preflight / OPTIONS
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # 2) Public routes & static assets
        if _is_public(path):
            return await call_next(request)

        # 3) Local/dev bypasses
        if _dev_bypass(request):
            return await call_next(request)

        # 4) Authenticate
        presented = _get_presented_key(request)
        if not presented or not _constant_time_member(presented, API_KEYS):
            client = _extract_client_ip(request)
            security_logger.warning("Unauthorized request from %s path=%s", client, path)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        # 5) Rate-limit (sliding window)
        bucket = _rate_limit_id(presented, request)
        now = time.time()
        _cleanup_request_log(now)
        window = _request_log[bucket]

        # prune entries outside window
        while window and now - window[0] >= RATE_WINDOW_SECS:
            window.popleft()

        if len(window) >= RATE_LIMIT:
            reset_in = max(0, int(RATE_WINDOW_SECS - (now - window[0])))
            security_logger.warning("Rate limit exceeded for %s path=%s", bucket, path)
            headers = _rate_limit_headers(RATE_LIMIT, 0, reset_in)
            # Optional: include Retry-After for clients that honor it
            headers.setdefault("Retry-After", str(reset_in))
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429, headers=headers)

        window.append(now)

        # 6) Call downstream
        response: Response = await call_next(request)

        # 7) Attach rate-limit headers
        remaining = RATE_LIMIT - len(window)
        reset_in = max(0, int(RATE_WINDOW_SECS - (now - window[0])) if window else RATE_WINDOW_SECS)
        for k, v in _rate_limit_headers(RATE_LIMIT, remaining, reset_in).items():
            response.headers[k] = v

        return response
