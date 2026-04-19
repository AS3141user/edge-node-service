"""ONNX model loader and inference wrapper."""
from __future__ import annotations

import io
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "mnist.onnx"
INPUT_SHAPE = (1, 1, 28, 28)  # NCHW


@dataclass
class Prediction:
    label: int
    confidence: float
    latency_ms: float
    probabilities: list[float]


class MnistModel:
    """Thin wrapper around an ONNX Runtime session for MNIST."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # CPUExecutionProvider is the sane default for edge / container deploys.
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=so,
            providers=["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Decode bytes -> normalized (1,1,28,28) float32 tensor."""
        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((28, 28))
        arr = np.asarray(img, dtype=np.float32) / 255.0
        return arr.reshape(INPUT_SHAPE)

    def predict(self, image_bytes: bytes) -> Prediction:
        tensor = self.preprocess(image_bytes)

        start = time.perf_counter()
        (logits,) = self.session.run([self.output_name], {self.input_name: tensor})
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        logits = logits.squeeze()
        # Softmax for human-readable probabilities.
        exp = np.exp(logits - logits.max())
        probs = exp / exp.sum()
        label = int(probs.argmax())

        return Prediction(
            label=label,
            confidence=float(probs[label]),
            latency_ms=elapsed_ms,
            probabilities=[float(p) for p in probs],
        )