"""Prometheus metrics definitions and middleware."""
from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

# --- Metric definitions ---

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    labelnames=("method", "path", "status"),
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


def register_metrics(app: FastAPI) -> None:
    """Attach /metrics endpoint and a latency-tracking middleware."""

    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next: Callable):
        # Skip instrumenting the metrics endpoint itself (avoids noise)
        if request.url.path == "/metrics":
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start

        # Use route template when available (e.g. "/items/{id}"),
        # fall back to raw path. Prevents high-cardinality label explosion.
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)

        REQUEST_COUNT.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            path=path,
        ).observe(elapsed)

        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)