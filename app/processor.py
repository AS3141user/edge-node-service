from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass
class SensorStats:
    count: int = 0
    mean: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0


class SensorProcessor:
    """
    Keeps per-sensor running statistics in memory.

    Uses a simple running mean update:
        new_mean = old_mean + (x - old_mean) / n
    """

    def __init__(self, anomaly_sigma: float = 2.0, alert_threshold: float = 30.0) -> None:
        self.anomaly_sigma = anomaly_sigma
        self.alert_threshold = alert_threshold
        self._stats: dict[str, SensorStats] = {}
        self._lock = Lock()

    def process(self, sensor_id: str, value: float) -> dict[str, float | int | bool]:
        with self._lock:
            stats = self._stats.get(sensor_id)

            if stats is None:
                stats = SensorStats(
                    count=1,
                    mean=value,
                    min_value=value,
                    max_value=value,
                )
                self._stats[sensor_id] = stats

                return {
                    "count": stats.count,
                    "running_mean": stats.mean,
                    "min_value": stats.min_value,
                    "max_value": stats.max_value,
                    "anomaly": False,
                    "threshold_alert": value > self.alert_threshold,
                }

            previous_mean = stats.mean

            stats.count += 1
            stats.mean = stats.mean + (value - stats.mean) / stats.count
            stats.min_value = min(stats.min_value, value)
            stats.max_value = max(stats.max_value, value)

            anomaly = abs(value - previous_mean) > self.anomaly_sigma
            threshold_alert = value > self.alert_threshold

            return {
                "count": stats.count,
                "running_mean": stats.mean,
                "min_value": stats.min_value,
                "max_value": stats.max_value,
                "anomaly": anomaly,
                "threshold_alert": threshold_alert,
            }