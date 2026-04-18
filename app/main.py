"""Edge Node Service — FastAPI entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app.metrics import register_metrics

app = FastAPI(
    title="Edge Node Service",
    version="0.1.0",
    description="Lightweight inference service for edge deployments.",
)

register_metrics(app)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}