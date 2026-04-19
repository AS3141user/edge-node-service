from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    sensor_id: str = Field(..., min_length=1, description="Unique sensor identifier.")
    value: float = Field(..., description="Raw sensor reading value.")
    timestamp: datetime = Field(..., description="Timestamp sent by the sensor.")


class ProcessingResponse(BaseModel):
    sensor_id: str
    input_value: float
    received_timestamp: datetime
    processed_at: datetime

    count: int
    running_mean: float
    min_value: float
    max_value: float
    anomaly: bool
    threshold_alert: bool