import pytest

from app.tests.framework.infrastructure.mock_factory import MockFactory
from app.tests.framework.infrastructure.performance import PerformanceTracker


@pytest.fixture
def mock_services():
    with MockFactory.mock_services() as mocks:
        yield mocks


@pytest.fixture
def performance_tracker():
    tracker = PerformanceTracker()
    yield tracker

    # Log metrics for debugging
    for metric in tracker.get_metrics():
        print(f"Performance: {metric.name} = {metric.value}{metric.unit}")


@pytest.fixture
def mock_vault_manager():
    return MockFactory.create_mock_vault_manager()


@pytest.fixture
def mock_task_service():
    return MockFactory.create_mock_task_service()
