import logging
import os
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ["TESTING"] = "true"

pytest_plugins = [
    "app.tests.framework.fixtures.environment_fixtures",
    "app.tests.framework.fixtures.api_fixtures",
    "app.tests.framework.fixtures.service_fixtures",
    "app.tests.framework.fixtures.data_fixtures",
]


@pytest.fixture(autouse=True)
def clean_test_environment():
    from app.tests.framework.infrastructure.context import TestContext

    if hasattr(TestContext, "clear"):
        TestContext.clear()

    yield


@pytest.fixture(scope="session")
def test_config():
    from app.tests.tests_config import TestStandards

    return TestStandards


@pytest.fixture
def perf():
    from app.tests.framework.infrastructure.performance import PerformanceTracker

    tracker = PerformanceTracker()
    yield tracker

    metrics = tracker.get_metrics()
    if metrics:
        print("\nPerformance Metrics:")
        for metric in metrics:
            status = (
                "✅"
                if not metric.threshold or metric.value <= metric.threshold
                else "❌"
            )
            print(f"  {status} {metric.name}: {metric.value:.2f}{metric.unit}")


@pytest.fixture
def error_scenarios():
    from app.tests.framework.scenarios.error_scenarios import ErrorScenarios

    return ErrorScenarios


def pytest_configure(config):
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "performance" in item.nodeid or "perf" in str(item.function.__name__):
            item.add_marker(pytest.mark.performance)

        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        setattr(item, "rep_" + rep.when, rep)

        try:
            from app.tests.framework.infrastructure.context import TestContext

            if hasattr(TestContext, "get_current"):
                context = TestContext.get_current()
                if context and hasattr(context, "metadata"):
                    rep.user_properties.append(("test_metadata", str(context.metadata)))
        except Exception as e:
            logging.getLogger(__name__).debug(f"Failed to get test context: {e}")
