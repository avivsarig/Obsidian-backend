from typing import Callable, Protocol, TypeVar

from app.src.domain.entities import TaskItem

T = TypeVar("T")


class TaskRepository(Protocol):
    """Repository interface for task persistence operations."""

    def get_tasks_from_folder(self, folder: str) -> list[TaskItem]:
        """Get all tasks from specified folder."""
        ...

    def find_task_by_id(self, task_id: str, folders: list[str]) -> TaskItem | None:
        """Find task by ID across multiple folders."""
        ...

    def save_task(self, task: TaskItem, target_folder: str) -> None:
        """Save task to specified folder."""
        ...

    def move_task(self, task: TaskItem, destination_folder: str) -> None:
        """Move task to different folder."""
        ...

    def delete_task(self, task: TaskItem) -> None:
        """Delete task."""
        ...


class ArchiveRepository(Protocol):
    """Repository interface for archive operations."""

    def archive_item(self, item, target_folder: str) -> None:
        """Archive an item to specified folder."""
        ...


class GitRepository(Protocol):
    """Repository interface for git operations."""

    def with_batch_sync(self, operation_func: Callable[[], T]) -> T:
        """Execute operation within git batch sync context."""
        ...
