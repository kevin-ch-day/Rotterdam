from __future__ import annotations

import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .context import set_request_id

request_logger = logging.getLogger("rotterdam.request")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        try:
            response: Response = await call_next(request)
        except Exception:
            response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
            response.headers["X-Request-ID"] = req_id
            request_logger.exception("%s %s - id=%s", request.method, request.url.path, req_id)
            return response
        response.headers["X-Request-ID"] = req_id
        request_logger.info("%s %s - id=%s", request.method, request.url.path, req_id)
        return response
