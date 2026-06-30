"""Readmint FastAPI application — routers, static mount, metrics, health."""
from __future__ import annotations

import logging
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import settings
from .core import templates as templates_mod
from .cortex_client import cortex
from .observability import setup_logging, setup_metrics
from .routers import batch, export, github, refine, score
from .services import history

setup_logging()
log = structlog.get_logger("readmint")

app = FastAPI(
    title="Readmint",
    version=__version__,
    description="README refinement with a deterministic no-loss guard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "dev" else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
for r in (refine.router, score.router, batch.router, github.router, export.router):
    app.include_router(r)


@app.get("/healthz", tags=["ops"])
async def healthz():
    return {
        "status": "ok",
        "version": __version__,
        "llm": cortex.provider(),
        "addons": {
            "cache": settings.cache_enabled,
            "history": settings.history_enabled,
            "github": settings.github_enabled,
            "confluence": settings.confluence_enabled,
            "auth": settings.auth_enabled,
        },
    }


@app.get("/api/templates", tags=["templates"])
async def list_templates():
    return {"templates": templates_mod.list_templates()}


@app.get("/api/llm", tags=["llm"])
async def llm_info():
    """Active provider (stub | cortex | local), selectable models, default pick.

    The UI uses this to populate the model selector when a local LLM is in use."""
    return cortex.provider_info()


@app.get("/api/history", tags=["history"])
async def get_history(limit: int = 50):
    return {"runs": history.list_runs(limit)}


# Prometheus /metrics
setup_metrics(app)

# Serve the built frontend if present (single-container deployment).
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
    log.info("frontend.mounted", path=str(_dist))


logging.getLogger("readmint").info("Readmint %s started (env=%s)", __version__, settings.environment)
