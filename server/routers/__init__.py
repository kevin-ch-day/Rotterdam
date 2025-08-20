"""API routers for the Rotterdam server."""

from .devices import router as devices_router
from .jobs import router as jobs_router
from .reports import router as reports_router
from .analytics import router as analytics_router
from .system import router as system_router

__all__ = [
    "devices_router",
    "jobs_router",
    "reports_router",
    "analytics_router",
    "system_router",
]
