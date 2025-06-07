import logging
from typing import cast

from app.src.core.exceptions.item_exceptions import ItemNotFoundError
from app.src.domain.date_service import DateService
from app.src.domain.entities import TaskItem
from app.src.domain.task_processor import TaskProcessor
from app.src.infrastructure.git.git_manager import GitManager
from app.src.infrastructure.vault_manager import VaultManager
from app.src.models.api_models import ProcessingResponse, TaskListResponse, TaskResponse

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        vault_manager: VaultManager,
        task_processor: TaskProcessor,
        config: dict,
        git_manager: GitManager | None = None,
    ):
        self.vault = vault_manager
        self.processor = task_processor
        self.config = config
        self.git = git_manager

    def list_tasks(self, include_completed: bool = True) -> TaskListResponse:
        active_tasks = self._get_tasks_from_folder(self.config["tasks"])
        completed_tasks = (
            self._get_tasks_from_folder(self.config["completed_tasks"])
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
        folders = [self.config["tasks"], self.config["completed_tasks"]]

        for folder in folders:
            task = self._find_task_in_folder(task_id, folder)
            if task:
                return TaskResponse.from_task_item(task)

        raise ItemNotFoundError(
            message=f"Task '{task_id}' not found",
            item_type="task",
            item_id=task_id,
        )

    def process_active_tasks(self) -> ProcessingResponse:
        active_tasks = self._get_tasks_from_folder(self.config["tasks"])

        if self.git:
            with self.git.batch_sync():
                processed_count = self._process_active_tasks_batch(active_tasks)

        else:
            processed_count = self._process_active_tasks_batch(active_tasks)

        return ProcessingResponse(
            processed=processed_count,
            message=f"Processed {processed_count} active tasks",
        )

    def _process_active_tasks_batch(
        self,
        active_tasks: list[TaskItem],
    ) -> int:
        processed_count = 0

        for task in active_tasks:
            try:
                self.processor.process_active_task(
                    vault=self.vault,
                    task=task,
                    config=self.config,
                )
                processed_count += 1
                logger.info(f"Processed active task: {task.title}")

            except Exception as e:
                logger.error(f"Failed to process active task {task.title}: {e}")
                continue

        commit_timestamp = DateService.now_timestamp_str()
        if self.git:
            self.git.commit_changes(
                f"{commit_timestamp} - Processed {processed_count} active tasks"
            )

        return processed_count

    def process_completed_tasks(self) -> ProcessingResponse:
        completed_tasks = self._get_tasks_from_folder(self.config["completed_tasks"])

        if self.git:
            with self.git.batch_sync():
                processed_count = self._process_completed_tasks_batch(completed_tasks)
        else:
            processed_count = self._process_completed_tasks_batch(completed_tasks)

        return ProcessingResponse(
            processed=processed_count,
            message=f"Processed {processed_count} completed tasks",
        )

    def _process_completed_tasks_batch(
        self,
        completed_tasks: list[TaskItem],
    ) -> int:
        retent_for_days = self.config.get("retent_for_days", 14)
        processed_count = 0

        for task in completed_tasks:
            try:
                self.processor.process_completed_task(
                    vault=self.vault,
                    task=task,
                    config=self.config,
                    retent_for_days=retent_for_days,
                )
                processed_count += 1
                logger.info(f"Processed completed task: {task.title}")

            except Exception as e:
                logger.error(f"Failed to process completed task {task.title}: {e}")
                continue

        commit_timestamp = DateService.now_timestamp_str()
        if self.git:
            self.git.commit_changes(
                f"{commit_timestamp} - Processed {processed_count} completed tasks"
            )

        return processed_count

    def _get_tasks_from_folder(self, folder: str) -> list[TaskItem]:
        # cast() needed because VaultManager.get_notes() returns list[BaseItem]
        # TODO: Make VaultManager generic when type system complexity is warranted
        return cast(list[TaskItem], self.vault.get_notes(folder, TaskItem))

    def _find_task_in_folder(self, task_id: str, folder: str) -> TaskItem | None:
        try:
            task_file = self.vault.vault_path / folder / f"{task_id}.md"

            if not task_file.exists():
                return None

            return cast(TaskItem, self.vault.read_note(task_file, TaskItem))
        except Exception as e:
            logger.warning(f"Error reading task {task_id} from {folder}: {e}")
            return None
