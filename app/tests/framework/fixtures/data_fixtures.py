import pytest

from app.tests.framework.builders.archive_builder import ArchiveBuilder
from app.tests.framework.builders.task_builder import TaskBuilder


@pytest.fixture
def sample_task():
    return (
        TaskBuilder()
        .with_title("Sample Task")
        .with_content("Sample task content")
        .build()
    )


@pytest.fixture
def completed_task():
    return (
        TaskBuilder()
        .with_title("Completed Task")
        .with_content("This task is done")
        .as_completed()
        .build()
    )


@pytest.fixture
def project_task():
    return (
        TaskBuilder()
        .with_title("Project Task")
        .with_content("Project description")
        .as_project()
        .build()
    )


@pytest.fixture
def sample_archive():
    return (
        ArchiveBuilder()
        .with_title("Sample Archive")
        .with_content("Archived content")
        .with_tags(["archived", "test"])
        .build()
    )
