from app.src.domain.entities import TaskItem
from app.src.infrastructure.vault_manager import VaultManager
from app.tests.framework.assertions import (
    assert_task_equal,
    assert_vault_file_exists,
    assert_vault_file_not_exists,
)
from app.tests.framework.context import TestContext
from app.tests.framework.environment import test_environment
from app.tests.framework.test_helpers import (
    capture_vault_state,
    create_test_task,
    restore_vault_state,
)


def test_framework_basic_functionality():
    TestContext.new_context(test_name="framework_basic_test")
    TestContext.set_metadata("purpose", "framework verification")

    with test_environment.isolated_environment(profile_name="unit") as (
        vault_path,
        settings,
    ):
        assert vault_path.exists()
        assert (vault_path / "Tasks").exists()
        assert (vault_path / "Tasks" / "Completed").exists()
        assert (vault_path / "Knowledge Archive").exists()

        vault_manager = VaultManager(vault_path)

        test_task = create_test_task(
            title="Framework Test Task", content="Testing the framework", done=False
        )

        vault_manager.write_note(test_task, target_dir="Tasks")

        assert_vault_file_exists(vault_path, "Tasks/Framework Test Task.md")

        read_task = vault_manager.read_note(
            vault_path / "Tasks" / "Framework Test Task.md", TaskItem
        )
        assert_task_equal(read_task, test_task)

        trace = TestContext.get_request_trace()
        assert len(trace) > 0
        assert any("Created isolated vault" in entry for entry in trace)
        assert any("Created test task" in entry for entry in trace)


def test_framework_time_manipulation():
    # TODO: implement better time testing
    with test_environment.isolated_environment() as (vault_path, settings):
        vault_manager = VaultManager(vault_path)

        task = create_test_task(
            title="Time Test Task", completed_at="2025-06-18T14:30:00"
        )
        vault_manager.write_note(task, target_dir="Tasks")

        read_task = vault_manager.read_note(
            vault_path / "Tasks" / "Time Test Task.md", TaskItem
        )

        assert read_task.completed_at is not None
        assert str(read_task.completed_at).startswith("2025-06-18")


def test_framework_state_snapshots():
    with test_environment.isolated_environment() as (vault_path, settings):
        vault_manager = VaultManager(vault_path)

        task1 = create_test_task(title="Task One", content="First task")
        vault_manager.write_note(task1, target_dir="Tasks")

        snapshot = capture_vault_state(vault_path)

        task2 = create_test_task(title="Task Two", content="Second task")
        vault_manager.write_note(task2, target_dir="Tasks")

        assert_vault_file_exists(vault_path, "Tasks/Task One.md")
        assert_vault_file_exists(vault_path, "Tasks/Task Two.md")

        restore_vault_state(vault_path, snapshot)

        assert_vault_file_exists(vault_path, "Tasks/Task One.md")
        assert_vault_file_not_exists(vault_path, "Tasks/Task Two.md")


def test_framework_git_integration():
    with test_environment.isolated_environment(with_git=True) as (vault_path, settings):
        assert (vault_path / ".git").exists()

        git_manager = TestContext.get_metadata("git_manager")
        assert git_manager is not None
        assert git_manager.current_branch is not None


def test_framework_seeded_data():
    seed_data = {
        "Tasks": {
            "Sample Task": {
                "frontmatter": {
                    "done": False,
                    "is_project": False,
                    "do_date": "2025-06-18",
                },
                "content": "This is a sample task for testing",
            }
        },
        "Knowledge Archive": {"Sample Note": "This is sample archive content"},
    }

    with test_environment.isolated_environment(seed_data=seed_data) as (
        vault_path,
        settings,
    ):
        assert_vault_file_exists(vault_path, "Tasks/Sample Task.md")
        assert_vault_file_exists(vault_path, "Knowledge Archive/Sample Note.md")

        vault_manager = VaultManager(vault_path)
        task = vault_manager.read_note(
            vault_path / "Tasks" / "Sample Task.md", TaskItem
        )
        assert task.title == "Sample Task"
        assert task.content == "This is a sample task for testing"
        assert not task.done
        assert str(task.do_date).startswith("2025-06-18")


def test_framework_performance_tracking():
    TestContext.new_context()

    TestContext.track_performance_metric("operation_time", 150.5, "ms")
    TestContext.track_performance_metric("memory_usage", 2048, "bytes")

    metrics = TestContext.get_performance_metrics()
    assert len(metrics) == 2

    time_metric = next(m for m in metrics if m.name == "operation_time")
    assert time_metric.value == 150.5
    assert time_metric.unit == "ms"

    memory_metric = next(m for m in metrics if m.name == "memory_usage")
    assert memory_metric.value == 2048
    assert memory_metric.unit == "bytes"


if __name__ == "__main__":
    test_framework_basic_functionality()
    print("✅ Basic functionality test passed")

    test_framework_time_manipulation()
    print("✅ Time manipulation test passed")

    test_framework_state_snapshots()
    print("✅ State snapshot test passed")

    test_framework_git_integration()
    print("✅ Git integration test passed")

    test_framework_seeded_data()
    print("✅ Seeded data test passed")

    test_framework_performance_tracking()
    print("✅ Performance tracking test passed")

    print("\n🎉 All framework verification tests passed!")
