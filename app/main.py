"""Edge Node Service — FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Edge Node Service",
    description="Containerised edge sensor-processing service.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns a static OK payload."""
    return {"status": "ok"}