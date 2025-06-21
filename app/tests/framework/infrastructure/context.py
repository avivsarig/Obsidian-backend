import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

# TODO: clean up pre 3.9 typing
from typing import Any, Dict, List


@dataclass
class PerformanceMetric:
    name: str
    value: float
    timestamp: float
    unit: str = "ms"


@dataclass
class TestExecutionContext:
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_trace: List[str] = field(default_factory=list)
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)


def _create_default_context() -> TestExecutionContext:
    return TestExecutionContext()


_test_context: ContextVar[TestExecutionContext | None] = ContextVar(
    "test_context", default=None
)


class TestContext:
    @classmethod
    def get_current(cls) -> TestExecutionContext:
        context = _test_context.get(None)
        if context is None:
            context = _create_default_context()
            cls.set_current(context)
        return context

    @classmethod
    def set_current(cls, context: TestExecutionContext) -> None:
        _test_context.set(context)

    @classmethod
    def new_context(cls, **metadata) -> TestExecutionContext:
        context = TestExecutionContext()
        context.metadata.update(metadata)
        cls.set_current(context)
        return context

    @classmethod
    def set_metadata(cls, key: str, value: Any) -> None:
        context = cls.get_current()
        context.metadata[key] = value

    @classmethod
    def get_metadata(cls, key: str, default: Any = None) -> Any:
        context = cls.get_current()
        return context.metadata.get(key, default)

    @classmethod
    def add_trace(cls, operation: str) -> None:
        context = cls.get_current()
        timestamp = time.time() - context.start_time
        trace_entry = f"[{timestamp:.3f}s] {operation}"
        context.request_trace.append(trace_entry)

    @classmethod
    def get_request_trace(cls) -> List[str]:
        return cls.get_current().request_trace

    @classmethod
    def track_performance_metric(
        cls, metric: str, value: float, unit: str = "ms"
    ) -> None:
        context = cls.get_current()
        performance_metric = PerformanceMetric(
            name=metric, value=value, timestamp=time.time(), unit=unit
        )
        context.performance_metrics.append(performance_metric)

    @classmethod
    def get_performance_metrics(cls) -> List[PerformanceMetric]:
        return cls.get_current().performance_metrics

    @classmethod
    def clear_context(cls) -> None:
        cls.set_current(TestExecutionContext())
