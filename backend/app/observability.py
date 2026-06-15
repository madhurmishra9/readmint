"""Structured logging + Prometheus metrics.

Logs are JSON with a per-process logger; we deliberately never log README bodies
or secret matches — only masked types and counts. Custom counters give cost
visibility (LLM calls + retries).

Metrics are wired by hand with ``prometheus_client`` rather than a third-party
instrumentator, so we don't depend on FastAPI route internals (which change
between versions).
"""
from __future__ import annotations

import logging
import time

import structlog
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from .config import settings

# --- custom metrics (cost visibility) ---
LLM_CALLS = Counter("readmint_llm_calls_total", "LLM completion calls", ["mode"])
LLM_RETRIES = Counter("readmint_llm_retries_total", "Pipeline repair retries")
PIPELINE_RUNS = Counter("readmint_pipeline_runs_total", "Pipeline runs", ["status", "verified"])
PIPELINE_LATENCY = Histogram("readmint_pipeline_seconds", "Pipeline wall time")
SECRETS_BLOCKED = Counter("readmint_secrets_blocked_total", "Runs blocked on high-severity secrets")

# --- HTTP metrics ---
HTTP_REQUESTS = Counter("readmint_http_requests_total", "HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("readmint_http_request_seconds", "HTTP request latency", ["method", "path"])

_EXCLUDED = {"/metrics"}


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        cache_logger_on_first_use=True,
    )


def setup_metrics(app) -> None:
    @app.middleware("http")
    async def _metrics(request, call_next):
        if request.url.path in _EXCLUDED:
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        # use the route *template* (e.g. /api/refine) to keep label cardinality low
        path = getattr(route, "path", None) or request.url.path
        HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method, path).observe(elapsed)
        return response

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
