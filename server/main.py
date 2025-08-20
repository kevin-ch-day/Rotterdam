"""FastAPI application exposing Rotterdam's job and analytics API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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

# Serve static files for the web UI
app.mount("/static", StaticFiles(directory="ui"), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Return the main dashboard page."""
    return FileResponse(Path("ui/pages/index.html"))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Serve the favicon if present."""
    path = Path("ui/favicon.ico")
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404)
