import urllib
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.src.automation.classes import TaskItem
from app.src.core.config import Settings, get_settings
from app.src.core.dependencies import get_vault_config, get_vault_manager
from app.src.core.exceptions.item_exceptions import ItemNotFoundError

router = APIRouter()


class TaskResponse(BaseModel):
    title: str = Field(..., description="Task title")
    content: str = Field(..., description="Task content/description")
    is_project: bool = Field(..., description="Whether this is a project")
    do_date: str | None = Field(None, description="When to do this task (YYYY-MM-DD)")
    due_date: str | None = Field(None, description="When this task is due (YYYY-MM-DD)")
    completed_at: str | None = Field(None, description="When task was completed")
    done: bool = Field(..., description="Whether task is completed")
    is_high_priority: bool = Field(..., description="Whether task is high priority")
    repeat_task: str | None = Field(
        None, description="Cron expression for recurring tasks"
    )

    @classmethod
    def from_task_item(cls, task: TaskItem) -> "TaskResponse":
        return cls(
            title=task.title,
            content=task.content,
            is_project=task.is_project,
            do_date=str(task.do_date) if task.do_date else None,
            due_date=str(task.due_date) if task.due_date else None,
            completed_at=str(task.completed_at) if task.completed_at else None,
            done=task.done,
            is_high_priority=task.is_high_priority,
            repeat_task=task.repeat_task,
        )


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int = Field(..., description="Total number of tasks")
    active: int = Field(..., description="Number of active tasks")
    completed: int = Field(..., description="Number of completed tasks")


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    include_completed: Annotated[
        bool,
        Query(description="Include completed tasks"),
    ] = True,
    vault=Depends(get_vault_manager),  # noqa: B008
    config=Depends(get_vault_config),  # noqa: B008
) -> TaskListResponse:
    active_tasks: list[TaskItem] = vault.get_notes(
        config["tasks"],
        TaskItem,
    )

    completed_tasks: list[TaskItem] = []
    if include_completed:
        completed_tasks = vault.get_notes(
            config["completed_tasks"],
            TaskItem,
        )

    all_tasks = active_tasks + completed_tasks
    task_responses = [TaskResponse.from_task_item(task) for task in all_tasks]

    return TaskListResponse(
        tasks=task_responses,
        total=len(all_tasks),
        active=len(active_tasks),
        completed=len(completed_tasks),
    )


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    vault=Depends(get_vault_manager),  # noqa: B008
    config=Depends(get_vault_config),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
):
    decoded_task_id = urllib.parse.unquote(task_id)

    task_file = settings.vault_path / config["tasks"] / f"{decoded_task_id}.md"

    if not task_file.exists():
        task_file = (
            settings.vault_path / config["completed_tasks"] / f"{decoded_task_id}.md"
        )

    if not task_file.exists():
        raise ItemNotFoundError(
            message=f"Task {task_id} is not found",
            item_type="task",
            item_id=decoded_task_id,
        )

    task = vault.read_note(
        task_file,
        TaskItem,
    )
    return TaskResponse.from_task_item(task)
