"""Authentication, rate limiting and request ID middleware."""

from __future__ import annotations

import hmac
import logging
import os
import time
import uuid
from collections import defaultdict
from typing import Callable

import contextvars
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Simple API key used for demonstration. Can be overridden with the
# ``ROTTERDAM_API_KEY`` environment variable.
API_KEY = os.environ.get("ROTTERDAM_API_KEY", "secret")

# Allow up to 60 requests per minute per client IP by default.
RATE_LIMIT = int(os.environ.get("ROTTERDAM_RATE_LIMIT", 60))

# Track timestamps of requests per client IP.
_request_log: dict[str, list[float]] = defaultdict(list)

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

security_logger = logging.getLogger("rotterdam.security")
request_logger = logging.getLogger("rotterdam.request")


def get_request_id() -> str | None:
    """Return the request ID for the current context."""
    return _request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next: Callable):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        _request_id_ctx.set(req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        request_logger.info("%s %s - id=%s", request.method, request.url.path, req_id)
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Validate an API key and apply naive rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable):
        key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(key, API_KEY):
            client_ip = request.client.host if request.client else "unknown"
            security_logger.warning("Unauthorized request from %s", client_ip)
            raise HTTPException(status_code=401, detail="Unauthorized")

        client_ip = request.client.host if request.client else "anonymous"
        now = time.time()
        window = [ts for ts in _request_log[client_ip] if now - ts < 60]
        if len(window) >= RATE_LIMIT:
            security_logger.warning("Rate limit exceeded for %s", client_ip)
            raise HTTPException(status_code=429, detail="Too Many Requests")
        window.append(now)
        _request_log[client_ip] = window

        response = await call_next(request)
        remaining = max(RATE_LIMIT - len(window), 0)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
