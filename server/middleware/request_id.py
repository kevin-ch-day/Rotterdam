from __future__ import annotations

import contextvars
import logging
import uuid
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

__all__ = ["RequestIDMiddleware", "get_request_id"]

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

request_logger = logging.getLogger("rotterdam.request")


def get_request_id() -> str | None:
    """Return the request ID for the current context."""
    return _request_id_ctx.get()


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
            request_logger.exception(
                "%s %s - id=%s", request.method, request.url.path, req_id
            )
            return response
        response.headers["X-Request-ID"] = req_id
        request_logger.info(
            "%s %s - id=%s", request.method, request.url.path, req_id
        )
        return response
