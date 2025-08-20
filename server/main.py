"""FastAPI application exposing Rotterdam's job and analytics API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
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

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuthRateLimitMiddleware)

# Routers
app.include_router(devices_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(system_router)

# UI / static
app.mount("/ui", StaticFiles(directory="ui"), name="ui")
# Optional: keep a /static path for compatibility if your templates reference it
app.mount("/static", StaticFiles(directory="ui"), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Serve the web UI's main dashboard page."""
    return FileResponse(Path("ui/pages/index.html"))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Serve the favicon if present, else 404."""
    path = Path("ui/favicon.ico")
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="favicon not found")
