import logging
from typing import Callable, TypeVar, cast

from app.src.domain.entities import TaskItem
from app.src.infrastructure.git.git_manager import GitManager
from app.src.infrastructure.vault_manager import VaultManager

T = TypeVar("T")
logger = logging.getLogger(__name__)


class VaultTaskRepository:
    """Task repository implementation using VaultManager."""

    def __init__(self, vault_manager: VaultManager):
        self.vault = vault_manager

    def get_tasks_from_folder(self, folder: str) -> list[TaskItem]:
        """Get all tasks from specified folder."""
        # cast() needed because VaultManager.get_notes() returns list[BaseItem]
        # TODO: Make VaultManager generic when type system complexity is warranted
        return cast(list[TaskItem], self.vault.get_notes(folder, TaskItem))

    def find_task_by_id(self, task_id: str, folders: list[str]) -> TaskItem | None:
        """Find task by ID across multiple folders."""
        for folder in folders:
            try:
                task_file = self.vault.vault_path / folder / f"{task_id}.md"

                if not task_file.exists():
                    continue

                return cast(TaskItem, self.vault.read_note(task_file, TaskItem))
            except Exception as e:
                logger.warning(f"Error reading task {task_id} from {folder}: {e}")
                continue

        return None

    def save_task(self, task: TaskItem, target_folder: str) -> None:
        """Save task to specified folder."""
        self.vault.write_note(task, target_dir=target_folder)

    def move_task(self, task: TaskItem, destination_folder: str) -> None:
        """Move task to different folder."""
        self.vault.move_note(item=task, destination_dir=destination_folder)

    def delete_task(self, task: TaskItem) -> None:
        """Delete task."""
        self.vault.delete_note(task)


class VaultArchiveRepository:
    """Archive repository implementation using VaultManager."""

    def __init__(self, vault_manager: VaultManager):
        self.vault = vault_manager

    def archive_item(self, item, target_folder: str) -> None:
        """Archive an item to specified folder."""
        self.vault.write_note(item=item, target_dir=target_folder)


class GitRepositoryAdapter:
    """Git repository adapter wrapping GitManager."""

    def __init__(self, git_manager: GitManager):
        self.git_manager = git_manager

    def with_batch_sync(self, operation_func: Callable[[], T]) -> T:
        """Execute operation within git batch sync context."""
        with self.git_manager.batch_sync():
            return operation_func()
