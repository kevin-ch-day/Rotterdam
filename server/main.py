# server/main.py
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .constants import APP_NAME, APP_VERSION
from .middleware import DEFAULT_API_KEY, AuthRateLimitMiddleware, RequestIDMiddleware
from .routers import (
    analytics_router,
    devices_router,
    jobs_router,
    reports_router,
    system_router,
)

# ---------- Paths (robust to CWD) ----------
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
# NOTE: All static files must live under ``/ui/...`` relative to the repository
# root so that the mounts below can serve them correctly.
UI_DIR = (REPO_ROOT / "ui").resolve()
INDEX_HTML = UI_DIR / "pages" / "index.html"
FAVICON_ICO = UI_DIR / "favicon.ico"


def _mask_path(p: Path) -> str:
    """Return repo-relative path to avoid leaking full filesystem layout."""
    try:
        return str(p.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return f".../{p.name}"


# Optional base path if served behind a proxy (e.g., /rotterdam)
ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(title=APP_NAME, version=APP_VERSION, root_path=ROOT_PATH)

# ---------- Logging ----------
log = logging.getLogger("uvicorn.error")

# ---------- Middleware ----------
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuthRateLimitMiddleware)

# Light security & cache headers
_STATIC_PREFIXES = (
    "/ui/",
    "/static/",
    "/css/",
    "/js/",
    "/images/",
    "/img/",
    "/fonts/",
    "/partials/",
)


@app.middleware("http")
async def add_headers(request: Request, call_next):
    resp: Response = await call_next(request)
    # Security
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("X-XSS-Protection", "0")
    # Cache static assets
    if request.url.path.startswith(_STATIC_PREFIXES):
        resp.headers.setdefault("Cache-Control", "public, max-age=3600, immutable")
    return resp


# ---------- Routers ----------
app.include_router(devices_router)
app.include_router(jobs_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(system_router)  # owns /_healthz (and /_ready if present)

# ---------- Static mounts ----------
# Serve entire ui/ under both /ui and /static for compatibility.
# Use check_dir=False so startup won't crash if UI_DIR is missing (we log warnings).
app.mount("/ui", StaticFiles(directory=str(UI_DIR), check_dir=False), name="ui")
app.mount("/static", StaticFiles(directory=str(UI_DIR), check_dir=False), name="static")

# Conditionally mount common asset roots if those folders exist (prevents startup errors)
for mount, subdir in (
    ("/css", "css"),
    ("/js", "js"),
    ("/images", "images"),
    ("/img", "img"),
    ("/fonts", "fonts"),
    ("/partials", "partials"),
):
    d = UI_DIR / subdir
    if d.exists():
        app.mount(mount, StaticFiles(directory=str(d)), name=subdir)


# ---------- Startup diagnostics ----------
@app.on_event("startup")
async def _startup_checks() -> None:
    log.info("ROOT_PATH=%s", ROOT_PATH or "(none)")
    log.info("UI_DIR=%s exists=%s", UI_DIR, UI_DIR.exists())
    log.info("INDEX_HTML=%s exists=%s", INDEX_HTML, INDEX_HTML.exists())
    log.info("FAVICON_ICO=%s exists=%s", FAVICON_ICO, FAVICON_ICO.exists())
    if not UI_DIR.exists():
        log.warning("UI directory missing — static mounts will 404: %s", UI_DIR)
    if not INDEX_HTML.exists():
        log.warning("Index file missing — GET / will 500: %s", INDEX_HTML)
    api_key = os.getenv("ROTTERDAM_API_KEY", DEFAULT_API_KEY)
    disable_auth = os.getenv("DISABLE_AUTH", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not disable_auth and api_key == DEFAULT_API_KEY:
        log.critical(
            "ROTTERDAM_API_KEY is using the default value; set a custom key for production"
        )


# ---------- Diagnostics (protected by middleware unless you allowlist it there) ----------
@app.get("/_diag", include_in_schema=False)
async def diag() -> JSONResponse:
    return JSONResponse(
        {
            "root_path": ROOT_PATH,
            "ui_dir": _mask_path(UI_DIR),
            "index_html": {
                "path": _mask_path(INDEX_HTML),
                "exists": INDEX_HTML.exists(),
            },
            "favicon_ico": {
                "path": _mask_path(FAVICON_ICO),
                "exists": FAVICON_ICO.exists(),
            },
        }
    )


# ---------- Web UI entry ----------
@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    # Mask path to avoid leaking full FS layout
    masked = _mask_path(INDEX_HTML)
    raise HTTPException(status_code=500, detail=f"index not found at {masked}")


# Favicon (no union return annotation)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if FAVICON_ICO.exists():
        return FileResponse(str(FAVICON_ICO))
    return PlainTextResponse("favicon not found", status_code=404)
