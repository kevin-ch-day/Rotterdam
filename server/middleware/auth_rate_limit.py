from __future__ import annotations

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .policies import AuthPolicy, SimpleApiPolicy
from .rate_limiter import RateLimiter
from .settings import Settings, SettingsError

security_logger = logging.getLogger("rotterdam.security")


def _rate_limit_headers(limit: int, remaining: int, reset_in: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(remaining, 0)),
        "X-RateLimit-Reset": str(reset_in),
    }


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        settings: Settings | None = None,
        policy: AuthPolicy | None = None,
        limiter: RateLimiter | None = None,
    ):
        super().__init__(app)
        self.settings = settings or Settings.from_env()
        self.policy = policy or SimpleApiPolicy(self.settings)
        self.limiter = limiter or RateLimiter(self.settings)
        if not self.settings.disable_auth and not self.settings.api_keys:
            raise SettingsError("Authentication enabled but no API keys configured")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        if method == "OPTIONS":
            return await call_next(request)

        if self.settings.is_public(path):
            return await call_next(request)

        presented = self.settings.extract_api_key(request)
        ip = self.settings.client_ip(request)

        if self.policy.requires_auth(path, method):
            if not presented or not self.settings.valid_api_key(presented):
                security_logger.warning("Unauthorized request from %s path=%s", ip, path)
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        bucket = self.limiter.bucket_for(presented, ip)
        now = time.monotonic()
        self.limiter.cleanup(now)
        allowed, remaining, reset_in = self.limiter.allow(bucket, now)
        headers = _rate_limit_headers(self.settings.rate_limit, remaining, reset_in)
        if not allowed:
            security_logger.warning("Rate limit exceeded for %s path=%s", bucket, path)
            headers.setdefault("Retry-After", str(reset_in))
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429, headers=headers)

        response: Response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
