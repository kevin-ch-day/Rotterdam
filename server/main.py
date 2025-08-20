"""FastAPI application exposing Rotterdam's job and analytics API."""

from __future__ import annotations

from fastapi import FastAPI

from .middleware import AuthRateLimitMiddleware, RequestIDMiddleware
from .routers import (
    analytics_router,
    devices_router,
    jobs_router,
    reports_router,
    system_router,
)

app = FastAPI(title="Rotterdam API")
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuthRateLimitMiddleware)
app.include_router(devices_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(system_router)
