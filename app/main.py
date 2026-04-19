"""Edge Node Service — FastAPI entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.metrics import REQUEST_COUNT, register_metrics
from app.processor import SensorProcessor
from app.schemas import ProcessingResponse, SensorReading

logger = logging.getLogger("edge-node")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting sensor processor...")
    app.state.processor = SensorProcessor(anomaly_sigma=2.0, alert_threshold=30.0)
    logger.info("Sensor processor ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Edge Node Service",
    version="0.3.0",
    description="Lightweight edge HTTP service for processing sensor readings locally.",
    lifespan=lifespan,
)

register_metrics(app)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready() -> dict[str, str]:
    if not hasattr(app.state, "processor"):
        raise HTTPException(status_code=503, detail="processor not loaded")
    return {"status": "ready"}


@app.post("/data", response_model=ProcessingResponse, tags=["processing"])
def process_sensor_data(payload: SensorReading) -> ProcessingResponse:
    try:
        result = app.state.processor.process(payload.sensor_id, payload.value)

        processed_at = datetime.now(timezone.utc)

        if result["threshold_alert"]:
            logger.warning(
                "Threshold alert for sensor=%s value=%s",
                payload.sensor_id,
                payload.value,
            )

        logger.info(
            "Processed sensor=%s value=%s count=%s mean=%.4f anomaly=%s alert=%s",
            payload.sensor_id,
            payload.value,
            result["count"],
            result["running_mean"],
            result["anomaly"],
            result["threshold_alert"],
        )

        return ProcessingResponse(
            sensor_id=payload.sensor_id,
            input_value=payload.value,
            received_timestamp=payload.timestamp,
            processed_at=processed_at,
            count=result["count"],
            running_mean=result["running_mean"],
            min_value=result["min_value"],
            max_value=result["max_value"],
            anomaly=result["anomaly"],
            threshold_alert=result["threshold_alert"],
        )

    except Exception as exc:
        logger.exception("Sensor processing failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc