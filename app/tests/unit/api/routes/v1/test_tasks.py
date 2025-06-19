from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.src.core.dependencies import get_task_service
from app.src.main import app
from app.src.models.api_models import ProcessingResponse, TaskListResponse, TaskResponse
from app.tests.framework.builders.task_builder import TaskBuilder

client = TestClient(app)


def test_list_tasks_success():
    task = TaskBuilder().with_title("Test Task").build()
    task_response = TaskResponse(
        title=task.title,
        content=task.content,
        is_project=task.is_project,
        do_date=None,
        due_date=None,
        completed_at=None,
        done=task.done,
        is_high_priority=task.is_high_priority,
        repeat_task=task.repeat_task,
    )
    expected = TaskListResponse(
        tasks=[task_response],
        total=1,
        active=1,
        completed=0,
    )
    mock_service = MagicMock()
    mock_service.list_tasks.return_value = expected
    app.dependency_overrides[get_task_service] = lambda: mock_service
    response = client.get("/api/v1/tasks/")
    app.dependency_overrides = {}
    assert response.status_code == 200
    assert response.json() == expected.model_dump()


def test_get_task_success():
    task = TaskBuilder().with_title("Task 123").build()
    expected = TaskResponse(
        title=task.title,
        content=task.content,
        is_project=task.is_project,
        do_date=None,
        due_date=None,
        completed_at=None,
        done=task.done,
        is_high_priority=task.is_high_priority,
        repeat_task=task.repeat_task,
    )
    mock_service = MagicMock()
    mock_service.get_task_by_id.return_value = expected
    app.dependency_overrides[get_task_service] = lambda: mock_service
    response = client.get("/api/v1/tasks/123")
    app.dependency_overrides = {}
    assert response.status_code == 200
    assert response.json() == expected.model_dump()


def test_process_active_tasks_success():
    expected = ProcessingResponse(processed=2, message="Processed 2 active tasks")
    mock_service = MagicMock()
    mock_service.process_active_tasks.return_value = expected
    app.dependency_overrides[get_task_service] = lambda: mock_service
    response = client.post("/api/v1/tasks/process-active")
    app.dependency_overrides = {}
    assert response.status_code == 200
    assert response.json() == expected.model_dump()


def test_process_completed_tasks_success():
    expected = ProcessingResponse(processed=1, message="Processed 1 completed tasks")
    mock_service = MagicMock()
    mock_service.process_completed_tasks.return_value = expected
    app.dependency_overrides[get_task_service] = lambda: mock_service
    response = client.post("/api/v1/tasks/process-completed")
    app.dependency_overrides = {}
    assert response.status_code == 200
    assert response.json() == expected.model_dump()
