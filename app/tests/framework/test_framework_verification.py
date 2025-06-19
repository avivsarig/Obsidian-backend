from app.src.domain.entities import TaskItem
from app.src.infrastructure.vault_manager import VaultManager
from app.tests.framework import (
    DomainAssertions,
    EnvironmentFactory,
    TaskBuilder,
    VaultAssertions,
    VaultBuilder,
)


def test_framework_basic_functionality():
    with EnvironmentFactory.create_isolated("unit") as vault_env:
        VaultAssertions.assert_vault_structure(vault_env.vault_path)

        vault_manager = VaultManager(vault_env.vault_path)

        test_task = (
            TaskBuilder()
            .with_title("Framework Test Task")
            .with_content("Testing the framework")
            .build()
        )

        vault_manager.write_note(test_task, target_dir="Tasks")

        VaultAssertions.assert_file_exists(
            vault_env.vault_path, "Tasks/Framework Test Task.md"
        )

        read_task = vault_manager.read_note(
            vault_env.vault_path / "Tasks" / "Framework Test Task.md", TaskItem
        )
        DomainAssertions.assert_task_equal(read_task, test_task)


def test_framework_builders():
    task = (
        TaskBuilder()
        .with_title("Test Task")
        .with_content("Test content")
        .as_project()
        .with_due_date("2025-06-25")
        .build()
    )

    assert task.title == "Test Task"
    assert task.content == "Test content"
    assert task.is_project is True
    assert task.due_date == "2025-06-25"


def test_framework_vault_builder():
    with EnvironmentFactory.create_isolated("unit") as vault_env:
        (
            VaultBuilder(vault_env)
            .with_task("Daily Review", done=False, do_date="2025-06-18")
            .with_task("Project Task", is_project=True, done=False)
            .with_completed_task(
                "Old Task", done=True, completed_at="2025-06-10T15:00:00"
            )
            .build()
        )

        VaultAssertions.assert_file_exists(
            vault_env.vault_path, "Tasks/Daily Review.md"
        )
        VaultAssertions.assert_file_exists(
            vault_env.vault_path, "Tasks/Project Task.md"
        )
        VaultAssertions.assert_file_exists(
            vault_env.vault_path, "Tasks/Completed/Old Task.md"
        )


def test_framework_domain_assertions():
    task1 = TaskBuilder().with_title("Test Task").with_content("Content").build()
    task2 = TaskBuilder().with_title("Test Task").with_content("Content").build()
    task3 = TaskBuilder().with_title("Different").with_content("Content").build()

    DomainAssertions.assert_task_equal(task1, task2)

    try:
        DomainAssertions.assert_task_equal(task1, task3)
        raise AssertionError("Should have raised AssertionError")
    except AssertionError as e:
        if "Should have raised AssertionError" in str(e):
            raise
        assert "title:" in str(e)


if __name__ == "__main__":
    test_framework_basic_functionality()
    print("✅ Basic functionality test passed")

    test_framework_builders()
    print("✅ Builder test passed")

    test_framework_vault_builder()
    print("✅ VaultBuilder test passed")

    test_framework_domain_assertions()
    print("✅ Domain assertions test passed")

    print("\n🎉 All framework verification tests passed!")
