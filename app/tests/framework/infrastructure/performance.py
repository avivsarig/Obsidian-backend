from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator


@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str = "ms"
    threshold: float | None = None


class PerformanceTracker:
    def __init__(self) -> None:
        self._metrics: list[PerformanceMetric] = []

    @contextmanager
    def measure(
        self, name: str, threshold: float | None = None
    ) -> Generator[None, None, None]:
        start_time = time.time()
        try:
            yield
        finally:
            # Convert to ms
            elapsed = (time.time() - start_time) * 1000
            metric = PerformanceMetric(name, elapsed, "ms", threshold)
            self._metrics.append(metric)

    def get_metrics(self) -> list[PerformanceMetric]:
        return self._metrics.copy()

    def assert_under_threshold(self, metric_name: str, threshold_ms: float) -> None:
        metric = next((m for m in self._metrics if m.name == metric_name), None)
        assert metric is not None, f"Metric {metric_name} not found"
        assert (
            metric.value <= threshold_ms
        ), f"Performance threshold exceeded: {metric.value}ms > {threshold_ms}ms"

    def clear(self) -> None:
        self._metrics.clear()
