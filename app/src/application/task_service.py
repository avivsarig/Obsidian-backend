import logging

from app.src.core.exceptions.item_exceptions import ItemNotFoundError
from app.src.domain.entities import TaskItem
from app.src.domain.repositories import GitRepository, TaskRepository
from app.src.domain.task_processor import TaskProcessor
from app.src.models.api_models import ProcessingResponse, TaskListResponse, TaskResponse

logger = logging.getLogger(__name__)


class TaskApplicationService:
    """Application service for task operations following Clean Architecture."""

    def __init__(
        self,
        task_repository: TaskRepository,
        task_processor: TaskProcessor,
        config: dict,
        git_repository: GitRepository | None = None,
    ):
        self.task_repository = task_repository
        self.task_processor = task_processor
        self.config = config
        self.git_repository = git_repository

    def list_tasks(self, include_completed: bool = True) -> TaskListResponse:
        """List all tasks with optional completed tasks."""
        active_tasks = self.task_repository.get_tasks_from_folder(self.config["tasks"])
        completed_tasks = (
            self.task_repository.get_tasks_from_folder(self.config["completed_tasks"])
            if include_completed
            else []
        )

        all_tasks = active_tasks + completed_tasks
        task_responses = [TaskResponse.from_task_item(task) for task in all_tasks]

        return TaskListResponse(
            tasks=task_responses,
            total=len(all_tasks),
            active=len(active_tasks),
            completed=len(completed_tasks),
        )

    def get_task_by_id(self, task_id: str) -> TaskResponse:
        """Get specific task by ID."""
        folders = [self.config["tasks"], self.config["completed_tasks"]]

        task = self.task_repository.find_task_by_id(task_id, folders)
        if not task:
            raise ItemNotFoundError(
                message=f"Task '{task_id}' not found",
                item_type="task",
                item_id=task_id,
            )

        return TaskResponse.from_task_item(task)

    def process_active_tasks(self) -> ProcessingResponse:
        """Process all active tasks."""
        active_tasks = self.task_repository.get_tasks_from_folder(self.config["tasks"])

        if self.git_repository:

            def process_batch() -> ProcessingResponse:
                return self._process_active_tasks_batch(active_tasks)

            return self.git_repository.with_batch_sync(process_batch)
        else:
            return self._process_active_tasks_batch(active_tasks)

    def _process_active_tasks_batch(
        self, active_tasks: list[TaskItem]
    ) -> ProcessingResponse:
        """Process active tasks batch."""
        processed_count = 0

        for task in active_tasks:
            try:
                self.task_processor.process_active_task(task, self.config)
                processed_count += 1
                logger.info(f"Processed active task: {task.title}")

            except Exception as e:
                logger.error(f"Failed to process active task {task.title}: {e}")
                continue

        return ProcessingResponse(
            processed=processed_count,
            message=f"Processed {processed_count} active tasks",
        )

    def process_completed_tasks(self) -> ProcessingResponse:
        """Process all completed tasks."""
        completed_tasks = self.task_repository.get_tasks_from_folder(
            self.config["completed_tasks"]
        )

        if self.git_repository:

            def process_batch() -> ProcessingResponse:
                return self._process_completed_tasks_batch(completed_tasks)

            return self.git_repository.with_batch_sync(process_batch)
        else:
            return self._process_completed_tasks_batch(completed_tasks)

    def _process_completed_tasks_batch(
        self, completed_tasks: list[TaskItem]
    ) -> ProcessingResponse:
        """Process completed tasks batch."""
        retent_for_days = self.config.get("retent_for_days", 14)
        processed_count = 0

        for task in completed_tasks:
            try:
                self.task_processor.process_completed_task(
                    task,
                    self.config,
                    retent_for_days,
                )
                processed_count += 1
                logger.info(f"Processed completed task: {task.title}")

            except Exception as e:
                logger.error(f"Failed to process completed task {task.title}: {e}")
                continue

        return ProcessingResponse(
            processed=processed_count,
            message=f"Processed {processed_count} completed tasks",
        )
