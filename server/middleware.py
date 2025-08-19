"""Authentication and rate-limiting middleware for the API."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Simple API key used for demonstration. In production load from config.
API_KEY = "secret"

# Allow up to 60 requests per minute per client IP.
RATE_LIMIT = 60

# Track timestamps of requests per client IP.
_request_log: dict[str, list[float]] = defaultdict(list)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Validate an API key and apply naive rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable):
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")

        client_ip = request.client.host if request.client else "anonymous"
        now = time.time()
        window = [ts for ts in _request_log[client_ip] if now - ts < 60]
        if len(window) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests")
        window.append(now)
        _request_log[client_ip] = window

        return await call_next(request)
