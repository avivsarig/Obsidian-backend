# Testing Framework

## Overview

The testing framework provides comprehensive infrastructure for testing the Obsidian Task Automation API. It uses pytest fixtures, builder patterns, and specialized assertion classes to create maintainable and reliable tests.

## Architecture

The framework is organized into focused modules that support different testing needs:

**Assertions** (`assertions/`): Domain-specific assertion classes that provide detailed error messages for API responses, domain objects, and vault operations.

**Builders** (`builders/`): Builder pattern implementations for constructing test data with fluent APIs and sensible defaults.

**Infrastructure** (`infrastructure/`): Core testing infrastructure including environment management, performance tracking, API clients, and mock factories.

**Fixtures** (`fixtures/`): Pytest fixtures organized by purpose (environment, API, services, data) for easy test setup.

**Scenarios** (`scenarios/`): Pre-built error scenarios for testing failure conditions and edge cases.

**Utils** (`utils/`): Utility functions for common testing operations like time manipulation and condition waiting.

## Quick Start

### Basic Test Setup

```python
def test_task_creation(vault_env, sample_task):
    from app.src.infrastructure.vault_manager import VaultManager
    from app.tests.framework import VaultAssertions, DomainAssertions

    vault_manager = VaultManager(vault_env.vault_path)
    vault_manager.write_note(sample_task, "Tasks")

    VaultAssertions.assert_file_exists(vault_env.vault_path, "Tasks/Sample Task.md")

    read_task = vault_manager.read_note(vault_env.vault_path / "Tasks" / "Sample Task.md", TaskItem)
    DomainAssertions.assert_task_equal(read_task, sample_task)
```

### API Testing

```python
def test_task_endpoint(api_client, populated_vault):
    from app.tests.framework import APIAssertions

    response = api_client.get("/api/v1/tasks/")
    APIAssertions.assert_success(response)
    APIAssertions.assert_task_list_response(response, expected_count=3)
```

### Performance Testing

```python
def test_bulk_operations(vault_env, perf):
    with perf.measure("bulk_write", threshold=500):
        # Perform operations
        for i in range(100):
            task = TaskBuilder().with_title(f"Task {i}").build()
            vault_manager.write_note(task, "Tasks")

    perf.assert_under_threshold("bulk_write", 500)
```

## Component Details

### Assertions

Three specialized assertion classes provide detailed error messages:

**APIAssertions**: Validates HTTP responses and API contracts
```python
APIAssertions.assert_success(response, expected_status=200)
APIAssertions.assert_error(response, 404, "Task not found")
APIAssertions.assert_task_response(response, {"title": "Test Task", "done": False})
```

**DomainAssertions**: Compares domain objects with detailed field-level reporting
```python
DomainAssertions.assert_task_equal(actual_task, expected_task)
DomainAssertions.assert_archive_equal(actual_archive, expected_archive)
```

**VaultAssertions**: Validates vault file operations and structure
```python
VaultAssertions.assert_file_exists(vault_path, "Tasks/task.md")
VaultAssertions.assert_file_contains(vault_path, "Tasks/task.md", "expected content")
VaultAssertions.assert_vault_structure(vault_path)
```

### Builders

Builder pattern implementations create test data with fluent APIs:

**TaskBuilder**: Constructs TaskItem objects with method chaining
```python
task = (TaskBuilder()
    .with_title("Important Task")
    .with_content("Task description")
    .as_project()
    .with_due_date("2025-06-25")
    .with_repeat("0 9 * * 1")
    .build())
```

**VaultBuilder**: Populates vault environments with structured data
```python
(VaultBuilder(vault_env)
    .with_task("Daily Review", done=False, do_date="2025-06-18")
    .with_completed_task("Old Task", done=True, completed_at="2025-06-10T15:00:00")
    .with_archive("Project Notes", content="Archived project information")
    .build())
```

**ArchiveBuilder**: Creates ArchiveItem objects with proper metadata
```python
archive = (ArchiveBuilder()
    .with_title("Research Notes")
    .with_content("Research findings")
    .with_tags(["research", "important"])
    .with_url("https://example.com")
    .build())
```

### Infrastructure

Core infrastructure components provide testing foundations:

**EnvironmentFactory**: Creates isolated vault environments
```python
with EnvironmentFactory.create_isolated("unit") as vault_env:
    # Test runs in completely isolated environment
    # Automatic cleanup after test completion
```

**APIClient**: Provides HTTP client with authentication support
```python
# Unauthenticated client
client = APIClient(vault_env)

# Authenticated client
auth_client = APIClient(vault_env, api_key="test-key-123")
response = auth_client.get("/api/v1/tasks/")
```

**PerformanceTracker**: Measures and validates performance metrics
```python
tracker = PerformanceTracker()
with tracker.measure("operation_name", threshold=100):
    # Perform timed operation

tracker.assert_under_threshold("operation_name", 100)
```

**MockFactory**: Creates and manages service mocks
```python
with MockFactory.mock_services() as mocks:
    mocks["vault_manager"].get_notes.return_value = test_tasks
    # Test with mocked dependencies
```

**Git Mocking Utilities**: Specialized mocks for Git repository testing scenarios
```python
# Mock Git repository unavailable (ImportError simulation)
with mock_git_unavailable():
    # Test behavior when git module is not installed

# Mock functional Git repository
with mock_git_repo() as repo_mock:
    repo_mock.head.is_valid.return_value = True
    # Test with working git repository

# Mock Git repository errors
with mock_git_repo_error(Exception("Repository corrupted")):
    # Test error handling for git operations
```

### Fixtures

Pytest fixtures provide ready-to-use test components:

**Environment Fixtures** (`fixtures/environment_fixtures.py`):
- `vault_env`: Isolated vault environment
- `integration_env`: Environment with authentication enabled
- `populated_vault`: Vault pre-populated with test data

**API Fixtures** (`fixtures/api_fixtures.py`):
- `api_client`: Unauthenticated API client
- `authenticated_client`: API client with test credentials

**Data Fixtures** (`fixtures/data_fixtures.py`):
- `sample_task`: Basic task for testing
- `completed_task`: Task marked as completed
- `project_task`: Task configured as project
- `sample_archive`: Archive item for testing

**Service Fixtures** (`fixtures/service_fixtures.py`):
- `mock_services`: Complete set of mocked services
- `performance_tracker`: Performance measurement tools
- `mock_vault_manager`: Isolated vault manager mock

### Error Scenarios

Pre-built scenarios test failure conditions:

```python
def test_permission_error(vault_env, error_scenarios):
    with error_scenarios.vault_permission_error():
        # Test behavior when vault write fails

def test_network_failure(api_client, error_scenarios):
    with error_scenarios.network_timeout():
        # Test API behavior during network issues
```

Available scenarios:
- `vault_permission_error()`: Simulates file permission failures
- `disk_full_error()`: Simulates storage exhaustion
- `git_operation_error()`: Simulates Git operation failures
- `network_timeout()`: Simulates network connectivity issues

## Testing Patterns

### Unit Testing

Unit tests use minimal fixtures and focus on isolated components:

```python
def test_task_date_normalization(sample_task):
    from app.src.domain.date_service import get_date_service

    date_service = get_date_service()
    normalized = date_service.normalize_for_field("2025-06-18", "do_date")

    assert str(normalized).startswith("2025-06-18")
```

### Integration Testing

Integration tests use real components with mocked external dependencies:

```python
def test_task_processing_workflow(integration_env, sample_task):
    vault_manager = VaultManager(integration_env.vault_path)
    task_processor = TaskProcessor()

    vault_manager.write_note(sample_task, "Tasks")
    task_processor.process_active_task(vault_manager, sample_task, config)

    VaultAssertions.assert_file_exists(integration_env.vault_path, "Tasks/Sample Task.md")
```

### API Testing

API tests validate endpoints and response formats:

```python
def test_task_list_endpoint(authenticated_client, populated_vault):
    response = authenticated_client.get("/api/v1/tasks/")

    APIAssertions.assert_success(response)
    APIAssertions.assert_task_list_response(response)

    data = response.json()
    assert data["total"] > 0
    assert "tasks" in data
```

### Performance Testing

Performance tests measure and validate timing requirements:

```python
@pytest.mark.performance
def test_concurrent_file_operations(vault_env, perf):
    vault_manager = VaultManager(vault_env.vault_path)

    with perf.measure("concurrent_writes", threshold=1000):
        tasks = [TaskBuilder().with_title(f"Task {i}").build() for i in range(50)]
        for task in tasks:
            vault_manager.write_note(task, "Tasks")

    perf.assert_under_threshold("concurrent_writes", 1000)
```

## Configuration

### Test Profiles

The framework supports different testing profiles via `tests_config.py`:

- **unit**: Minimal setup, high mocking, no authentication
- **integration**: Real vault operations, medium mocking, authentication enabled
- **e2e**: Full stack testing, minimal mocking, all features enabled

### Performance Thresholds

Performance standards are defined in `tests_config.py`:

```python
PERFORMANCE_THRESHOLDS = {
    "vault_operations": {"max_time_ms": 500},
    "api_requests": {"max_time_ms": 1000},
    "file_operations": {"max_time_ms": 200},
}
```

### Test Data Templates

Standardized test data is available for consistent testing:

```python
# Use predefined templates
task_data = TestStandards.get_seed_data("realistic")

# Validate API coverage
coverage = TestStandards.validate_api_coverage(router_analysis)
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest app/tests/

# Run specific test types
pytest app/tests/ -m unit
pytest app/tests/ -m integration
pytest app/tests/ -m performance

# Run with coverage
pytest app/tests/ --cov=app/src --cov-report=term-missing
```

### Test Markers

Tests are automatically marked based on their location and naming:

- `@pytest.mark.unit`: Unit tests (automatic)
- `@pytest.mark.integration`: Integration tests (automatic)
- `@pytest.mark.performance`: Performance tests (automatic)
- `@pytest.mark.slow`: Long-running tests (manual)

### Debugging Failed Tests

The framework captures test metadata for debugging:

```bash
# Run with verbose output
pytest app/tests/ -v

# Capture performance metrics
pytest app/tests/ -s  # Shows performance output

# Run single test with full output
pytest app/tests/unit/test_specific.py::test_function -v -s
```

## File Structure

```
app/tests/framework/
├── assertions/
│   ├── api_assertions.py         # HTTP response validation
│   ├── domain_assertions.py      # Domain object comparison
│   └── vault_assertions.py       # File system validation
├── builders/
│   ├── archive_builder.py        # ArchiveItem construction
│   ├── task_builder.py          # TaskItem construction
│   └── vault_builder.py         # Vault population
├── fixtures/
│   ├── api_fixtures.py          # API client fixtures
│   ├── data_fixtures.py         # Test data fixtures
│   ├── environment_fixtures.py  # Environment setup
│   └── service_fixtures.py      # Service mocks
├── infrastructure/
│   ├── api_client.py            # HTTP client wrapper
│   ├── context.py               # Test execution context
│   ├── environment.py           # Environment management
│   ├── mock_factory.py          # Mock service creation
│   └── performance.py           # Performance measurement
├── scenarios/
│   └── error_scenarios.py       # Error condition simulation
├── utils/
│   └── test_helpers.py          # Utility functions
└── test_framework_verification.py # Framework self-tests
```

## Best Practices

**Use Appropriate Fixtures**: Choose fixtures that match your test scope. Use `vault_env` for unit tests, `integration_env` for integration tests.

**Leverage Builders**: Use builder pattern for creating test data. It provides better readability and maintainability than manual object construction.

**Validate with Assertions**: Use specialized assertion classes instead of generic asserts. They provide better error messages and understand domain semantics.

**Measure Performance**: Use the performance tracker for operations with timing requirements. Set appropriate thresholds based on `tests_config.py`.

**Mock Appropriately**: Use `MockFactory` for external dependencies. Keep mocking minimal in integration tests to verify real component interactions.

**Clean Up Resources**: Fixtures handle cleanup automatically, but complex tests should verify proper resource cleanup.

The framework handles environment isolation, resource cleanup, and test data management automatically, allowing tests to focus on business logic verification rather than infrastructure concerns.
