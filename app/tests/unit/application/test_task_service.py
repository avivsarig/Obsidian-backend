from unittest.mock import Mock, patch

import pytest

from app.src.application.task_service import TaskApplicationService
from app.src.core.exceptions.item_exceptions import ItemNotFoundError
from app.src.models.api_models import ProcessingResponse, TaskListResponse, TaskResponse
from app.tests.framework.builders.task_builder import TaskBuilder


class TestTaskApplicationService:
    @pytest.fixture
    def mock_task_repository(self):
        return Mock()

    @pytest.fixture
    def mock_task_processor(self):
        return Mock()

    @pytest.fixture
    def mock_git_repository(self):
        return Mock()

    @pytest.fixture
    def test_config(self):
        return {
            "tasks": "Tasks/",
            "completed_tasks": "Tasks/Completed/",
            "retention_for_days": 14,
        }

    @pytest.fixture
    def service(self, mock_task_repository, mock_task_processor, test_config):
        return TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=test_config,
        )

    @pytest.fixture
    def service_with_git(
        self,
        mock_task_repository,
        mock_task_processor,
        test_config,
        mock_git_repository,
    ):
        return TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=test_config,
            git_repository=mock_git_repository,
        )

    @pytest.fixture
    def sample_tasks(self):
        return [
            TaskBuilder().with_title("Task 1").build(),
            TaskBuilder().with_title("Task 2").as_completed().build(),
            TaskBuilder().with_title("Task 3").as_project().build(),
        ]

    def test_init_without_git(
        self, mock_task_repository, mock_task_processor, test_config
    ):
        service = TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=test_config,
        )

        assert service.task_repository == mock_task_repository
        assert service.task_processor == mock_task_processor
        assert service.config == test_config
        assert service.git_repository is None

    def test_init_with_git(
        self,
        mock_task_repository,
        mock_task_processor,
        test_config,
        mock_git_repository,
    ):
        service = TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=test_config,
            git_repository=mock_git_repository,
        )

        assert service.git_repository == mock_git_repository

    def test_list_tasks_with_completed(
        self, service, mock_task_repository, sample_tasks
    ):
        active_tasks = [sample_tasks[0], sample_tasks[2]]
        completed_tasks = [sample_tasks[1]]

        mock_task_repository.get_tasks_from_folder.side_effect = [
            active_tasks,
            completed_tasks,
        ]

        result = service.list_tasks(include_completed=True)

        assert isinstance(result, TaskListResponse)
        assert result.total == 3
        assert result.active == 2
        assert result.completed == 1
        assert len(result.tasks) == 3

        mock_task_repository.get_tasks_from_folder.assert_any_call("Tasks/")
        mock_task_repository.get_tasks_from_folder.assert_any_call("Tasks/Completed/")

    def test_list_tasks_without_completed(
        self, service, mock_task_repository, sample_tasks
    ):
        active_tasks = [sample_tasks[0], sample_tasks[2]]

        mock_task_repository.get_tasks_from_folder.return_value = active_tasks

        result = service.list_tasks(include_completed=False)

        assert isinstance(result, TaskListResponse)
        assert result.total == 2
        assert result.active == 2
        assert result.completed == 0
        assert len(result.tasks) == 2

        mock_task_repository.get_tasks_from_folder.assert_called_once_with("Tasks/")

    def test_get_task_by_id_found(self, service, mock_task_repository, sample_tasks):
        task = sample_tasks[0]
        mock_task_repository.find_task_by_id.return_value = task

        result = service.get_task_by_id("task-1")

        assert isinstance(result, TaskResponse)
        assert result.title == "Task 1"

        mock_task_repository.find_task_by_id.assert_called_once_with(
            "task-1", ["Tasks/", "Tasks/Completed/"]
        )

    def test_get_task_by_id_not_found(self, service, mock_task_repository):
        mock_task_repository.find_task_by_id.return_value = None

        with pytest.raises(ItemNotFoundError) as exc_info:
            service.get_task_by_id("nonexistent-task")

        assert exc_info.value.item_type == "task"
        assert exc_info.value.item_id == "nonexistent-task"
        assert "Task 'nonexistent-task' not found" in str(exc_info.value)

    def test_process_active_tasks_without_git(
        self, service, mock_task_repository, mock_task_processor, sample_tasks
    ):
        active_tasks = [sample_tasks[0], sample_tasks[2]]
        mock_task_repository.get_tasks_from_folder.return_value = active_tasks

        result = service.process_active_tasks()

        assert isinstance(result, ProcessingResponse)
        assert result.processed == 2
        assert "Processed 2 active tasks" in result.message

        assert mock_task_processor.process_active_task.call_count == 2
        mock_task_processor.process_active_task.assert_any_call(
            sample_tasks[0], service.config
        )
        mock_task_processor.process_active_task.assert_any_call(
            sample_tasks[2], service.config
        )

    def test_process_active_tasks_with_git(
        self,
        service_with_git,
        mock_task_repository,
        mock_task_processor,
        mock_git_repository,
        sample_tasks,
    ):
        active_tasks = [sample_tasks[0]]
        mock_task_repository.get_tasks_from_folder.return_value = active_tasks

        def mock_batch_sync(callback):
            return callback()

        mock_git_repository.with_batch_sync.side_effect = mock_batch_sync

        result = service_with_git.process_active_tasks()

        assert isinstance(result, ProcessingResponse)
        assert result.processed == 1

        mock_git_repository.with_batch_sync.assert_called_once()
        mock_task_processor.process_active_task.assert_called_once_with(
            sample_tasks[0], service_with_git.config
        )

    @patch("app.src.application.task_service.logger")
    def test_process_active_tasks_with_errors(
        self,
        mock_logger,
        service,
        mock_task_repository,
        mock_task_processor,
        sample_tasks,
    ):
        active_tasks = [sample_tasks[0], sample_tasks[2]]
        mock_task_repository.get_tasks_from_folder.return_value = active_tasks

        mock_task_processor.process_active_task.side_effect = [
            None,  # First task succeeds
            Exception("Processing failed"),  # Second task fails
        ]

        result = service.process_active_tasks()

        assert result.processed == 1
        assert "Processed 1 active tasks" in result.message

        mock_logger.info.assert_called_once_with("Processed active task: Task 1")
        mock_logger.error.assert_called_once_with(
            "Failed to process active task Task 3: Processing failed"
        )

    def test_process_completed_tasks_without_git(
        self, service, mock_task_repository, mock_task_processor, sample_tasks
    ):
        completed_tasks = [sample_tasks[1]]
        mock_task_repository.get_tasks_from_folder.return_value = completed_tasks

        result = service.process_completed_tasks()

        assert isinstance(result, ProcessingResponse)
        assert result.processed == 1
        assert "Processed 1 completed tasks" in result.message

        mock_task_processor.process_completed_task.assert_called_once_with(
            sample_tasks[1], service.config, 14
        )

    def test_process_completed_tasks_with_git(
        self,
        service_with_git,
        mock_task_repository,
        mock_task_processor,
        mock_git_repository,
        sample_tasks,
    ):
        completed_tasks = [sample_tasks[1]]
        mock_task_repository.get_tasks_from_folder.return_value = completed_tasks

        def mock_batch_sync(callback):
            return callback()

        mock_git_repository.with_batch_sync.side_effect = mock_batch_sync

        result = service_with_git.process_completed_tasks()

        assert isinstance(result, ProcessingResponse)
        assert result.processed == 1

        mock_git_repository.with_batch_sync.assert_called_once()
        mock_task_processor.process_completed_task.assert_called_once_with(
            sample_tasks[1], service_with_git.config, 14
        )

    def test_process_completed_tasks_custom_retention(
        self, mock_task_repository, mock_task_processor, sample_tasks
    ):
        config = {
            "tasks": "Tasks/",
            "completed_tasks": "Tasks/Completed/",
            "retention_for_days": 30,
        }

        service = TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=config,
        )

        completed_tasks = [sample_tasks[1]]
        mock_task_repository.get_tasks_from_folder.return_value = completed_tasks

        result = service.process_completed_tasks()

        assert result.processed == 1
        mock_task_processor.process_completed_task.assert_called_once_with(
            sample_tasks[1], config, 30
        )

    def test_process_completed_tasks_default_retention(
        self, mock_task_repository, mock_task_processor, sample_tasks
    ):
        config = {
            "tasks": "Tasks/",
            "completed_tasks": "Tasks/Completed/",
        }

        service = TaskApplicationService(
            task_repository=mock_task_repository,
            task_processor=mock_task_processor,
            config=config,
        )

        completed_tasks = [sample_tasks[1]]
        mock_task_repository.get_tasks_from_folder.return_value = completed_tasks

        result = service.process_completed_tasks()

        assert result.processed == 1
        mock_task_processor.process_completed_task.assert_called_once_with(
            sample_tasks[1], config, 14
        )

    @patch("app.src.application.task_service.logger")
    def test_process_completed_tasks_with_errors(
        self,
        mock_logger,
        service,
        mock_task_repository,
        mock_task_processor,
        sample_tasks,
    ):
        completed_tasks = [sample_tasks[1]]
        mock_task_repository.get_tasks_from_folder.return_value = completed_tasks

        mock_task_processor.process_completed_task.side_effect = Exception(
            "Archive failed"
        )

        result = service.process_completed_tasks()

        assert result.processed == 0
        assert "Processed 0 completed tasks" in result.message

        mock_logger.error.assert_called_once_with(
            "Failed to process completed task Task 2: Archive failed"
        )

    def test_process_active_tasks_empty_list(
        self, service, mock_task_repository, mock_task_processor
    ):
        mock_task_repository.get_tasks_from_folder.return_value = []

        result = service.process_active_tasks()

        assert result.processed == 0
        assert "Processed 0 active tasks" in result.message
        mock_task_processor.process_active_task.assert_not_called()

    def test_process_completed_tasks_empty_list(
        self, service, mock_task_repository, mock_task_processor
    ):
        mock_task_repository.get_tasks_from_folder.return_value = []

        result = service.process_completed_tasks()

        assert result.processed == 0
        assert "Processed 0 completed tasks" in result.message
        mock_task_processor.process_completed_task.assert_not_called()

    def test_list_tasks_empty_folders(self, service, mock_task_repository):
        mock_task_repository.get_tasks_from_folder.return_value = []

        result = service.list_tasks()

        assert result.total == 0
        assert result.active == 0
        assert result.completed == 0
        assert len(result.tasks) == 0

    def test_task_response_conversion(
        self, service, mock_task_repository, sample_tasks
    ):
        active_tasks = [sample_tasks[0]]
        completed_tasks = []

        mock_task_repository.get_tasks_from_folder.side_effect = [
            active_tasks,
            completed_tasks,
        ]

        result = service.list_tasks()

        assert len(result.tasks) == 1
        task_response = result.tasks[0]
        assert isinstance(task_response, TaskResponse)
        assert task_response.title == "Task 1"
        assert not task_response.is_project
        assert not task_response.done
