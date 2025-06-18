# Testing Framework

## Overview

The testing framework provides infrastructure for comprehensive testing of the Obsidian Task Automation API. It creates isolated test environments, manages test data, and provides domain-specific assertions for reliable test execution.

## Architecture

The framework consists of five core components that work together to enable different testing scenarios:

**Test Environment Management** (`environment.py`): Creates isolated vault environments with configurable profiles, optional git integration, and data seeding capabilities.

**Configuration Management** (`config.py`): Manages test-specific settings with environment profiles and setting overrides for different test scenarios.

**Execution Context** (`context.py`): Tracks test execution state, performance metrics, and operation traces using thread-safe context variables.

**Domain Assertions** (`assertions.py`): Provides specialized assertion functions for TaskItem, ArchiveItem, and vault file operations with detailed error reporting.

**Test Utilities** (`test_helpers.py`): Offers helper functions for time manipulation, state management, test data creation, and condition waiting.

## Component Details

### Environment Management

The `TestEnvironmentManager` creates isolated test environments to prevent test interference:

```python
from app.tests.framework import test_environment

# Create isolated environment with automatic cleanup
with test_environment.isolated_environment(profile_name="unit") as (vault_path, settings):
    # Test code runs in completely isolated vault
    vault_manager = VaultManager(vault_path)
    # Changes are automatically cleaned up after test
```

**Environment Profiles**: Three predefined profiles optimize for different test types:
- `unit`: Minimal setup with authentication disabled
- `integration`: Full vault with authentication and rate limiting enabled
- `e2e`: Complete environment for end-to-end testing

**Git Integration**: Optional git repository initialization for testing version control workflows:

```python
with test_environment.isolated_environment(with_git=True) as (vault_path, settings):
    git_manager = TestContext.get_metadata("git_manager")
    # Git operations work normally within test environment
```

**Data Seeding**: Pre-populate vaults with structured test data:

```python
seed_data = {
    "Tasks": {
        "Sample Task": {
            "frontmatter": {"done": False, "do_date": "2025-06-18"},
            "content": "Task description"
        }
    }
}

with test_environment.isolated_environment(seed_data=seed_data) as (vault_path, settings):
    # Vault contains pre-created files
```

### Configuration Management

The `TestConfigManager` handles environment-specific configurations:

```python
from app.tests.framework import test_config

# Override specific settings for test
with test_config.override_settings(vault_path="/tmp/test", require_auth=False) as settings:
    # Settings object has overridden values
    assert settings.require_auth == False
```

**Feature Toggles**: Enable or disable features during testing:

```python
test_config.enable_feature_toggle("experimental_feature")
if test_config.is_feature_enabled("experimental_feature"):
    # Feature-specific test logic
```

### Execution Context

The `TestContext` tracks test execution state and performance:

```python
from app.tests.framework import TestContext

# Create new test context with metadata
TestContext.new_context(test_name="integration_test", component="task_processor")

# Track operations and performance
TestContext.add_trace("Starting task processing")
TestContext.track_performance_metric("processing_time", 150.5, "ms")

# Retrieve execution information
trace = TestContext.get_request_trace()
metrics = TestContext.get_performance_metrics()
```

The context uses `contextvars` for thread safety, ensuring each test maintains independent execution state.

### Domain Assertions

Specialized assertions provide detailed error messages for domain objects:

```python
from app.tests.framework import assert_task_equal, assert_vault_file_exists

# Compare TaskItem objects with comprehensive field validation
expected_task = create_test_task(title="Test Task", done=True)
actual_task = vault_manager.read_note(task_path, TaskItem)
assert_task_equal(actual_task, expected_task)

# Verify vault file operations
assert_vault_file_exists(vault_path, "Tasks/Test Task.md")
assert_vault_file_contains(vault_path, "Tasks/Test Task.md", "expected content")
```

**Error Reporting**: Assertions provide structured error messages showing exactly which fields differ:

```
TaskItem mismatch for 'Test Task':
  • done: got False, expected True
  • do_date: got '2025-06-19', expected '2025-06-18'
```

### Test Utilities

Helper functions simplify common testing operations:

```python
from app.tests.framework import freeze_time, capture_vault_state, create_test_task

# Time manipulation for date-dependent logic
with freeze_time(datetime(2025, 6, 18, 14, 30)):
    # All datetime.now() calls return frozen time
    task_processor.process_active_task(task)

# State management for rollback testing
snapshot = capture_vault_state(vault_path)
# Make changes that should be reverted
restore_vault_state(vault_path, snapshot)

# Create test data with sensible defaults
task = create_test_task(title="Integration Test", done=False)
```

## Usage Patterns

### Unit Testing

Unit tests use minimal environment setup with mocked dependencies:

```python
def test_task_date_normalization():
    with test_environment.isolated_environment(profile_name="unit") as (vault_path, settings):
        vault_manager = VaultManager(vault_path)

        task = create_test_task(do_date="2025-06-18")
        vault_manager.write_note(task, "Tasks")

        read_task = vault_manager.read_note(vault_path / "Tasks" / "test-task.md", TaskItem)
        assert str(read_task.do_date).startswith("2025-06-18")
```

### Integration Testing

Integration tests use full environment with real service interactions:

```python
def test_task_processing_workflow():
    with test_environment.isolated_environment(profile_name="integration", with_git=True) as (vault_path, settings):
        vault_manager = VaultManager(vault_path)
        task_processor = TaskProcessor()

        # Create and process task through complete workflow
        task = create_test_task(title="Integration Task", done=True)
        vault_manager.write_note(task, "Tasks")

        task_processor.process_active_task(vault_manager, task, config)

        # Verify task moved to completed folder
        assert_vault_file_exists(vault_path, "Tasks/Completed/Integration Task.md")
```

### Performance Testing

Performance tests track metrics and validate timing requirements:

```python
def test_concurrent_file_operations():
    TestContext.new_context(test_type="performance")

    with test_environment.isolated_environment() as (vault_path, settings):
        start_time = time.time()

        # Execute concurrent operations
        tasks = [create_test_task(title=f"Task {i}") for i in range(100)]
        for task in tasks:
            vault_manager.write_note(task, "Tasks")

        elapsed = (time.time() - start_time) * 1000
        TestContext.track_performance_metric("batch_write_time", elapsed, "ms")

        # Validate performance requirements
        metrics = TestContext.get_performance_metrics()
        batch_time = next(m for m in metrics if m.name == "batch_write_time")
        assert batch_time.value < 5000  # Under 5 seconds
```

## File Structure

```
app/tests/framework/
├── __init__.py                    # Framework exports
├── assertions.py                  # Domain-specific assertions
├── config.py                      # Configuration management
├── context.py                     # Execution context tracking
├── environment.py                 # Test environment management
├── test_helpers.py               # Utility functions
└── test_framework_verification.py # Framework self-tests
```

## Framework Verification

The framework includes self-verification tests to ensure all components function correctly:

```bash
python app/tests/framework/test_framework_verification.py
```

These tests verify:
- Environment isolation and cleanup
- Configuration override mechanisms
- Context tracking and performance metrics
- State snapshot and restoration
- Git integration functionality
- Data seeding capabilities

## Best Practices

**Environment Isolation**: Always use isolated environments to prevent test interference. The framework automatically creates temporary directories and cleans them up after test completion.

**Context Usage**: Leverage test context for debugging failed tests. The execution trace shows exactly which operations occurred and their timing.

**State Management**: Use state snapshots for tests that need to verify rollback behavior or test multiple scenarios from the same starting point.

**Performance Tracking**: Track performance metrics for operations that have timing requirements. The framework provides structured metric collection for analysis.

**Domain Assertions**: Use specialized assertions instead of generic asserts. They provide better error messages and understand domain object semantics.

The framework handles resource cleanup automatically, but complex tests should verify cleanup occurs properly to prevent resource leaks in test suites.
