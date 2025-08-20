"""FastAPI application exposing Rotterdam's job and analytics API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

app.mount("/ui", StaticFiles(directory="ui"), name="ui")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:  # pragma: no cover - trivial redirect
    """Serve the web UI's index page."""
    return FileResponse("ui/pages/index.html")
