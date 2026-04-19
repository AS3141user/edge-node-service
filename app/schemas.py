"""Pydantic response schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    label: int = Field(..., description="Predicted digit class (0–9).")
    confidence: float = Field(..., ge=0.0, le=1.0)
    latency_ms: float = Field(..., description="Model inference latency in ms.")
    probabilities: list[float] = Field(
        ..., description="Per-class softmax probabilities, index = class."
    )