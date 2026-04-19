"""Edge Node Service — FastAPI entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.metrics import INFERENCE_LATENCY, PREDICTION_COUNT, register_metrics
from app.model import MnistModel
from app.schemas import PredictionResponse

logger = logging.getLogger("edge-node")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_BYTES = 1 * 1024 * 1024  # 1 MB upload cap


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ONNX model...")
    app.state.model = MnistModel()
    logger.info("Model loaded: input=%s output=%s",
                app.state.model.input_name, app.state.model.output_name)
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Edge Node Service",
    version="0.2.0",
    description="Lightweight ONNX inference service for edge deployments.",
    lifespan=lifespan,
)

register_metrics(app)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready() -> dict[str, str]:
    """Readiness probe — true only once the model is loaded."""
    if not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="model not loaded")
    return {"status": "ready"}


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type: {file.content_type}",
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 1 MB).")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        result = app.state.model.predict(data)

        logger.info("Prediction result: %r", result)
        logger.info("Prediction result dict: %s", result.__dict__)

        INFERENCE_LATENCY.observe(result.latency_ms / 1000.0)
        PREDICTION_COUNT.labels(label=str(result.label)).inc()

        return PredictionResponse(**result.__dict__)

    except Exception as exc:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(exc)}") from exc