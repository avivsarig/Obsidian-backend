import urllib
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.src.core.config import Settings, get_settings
from app.src.core.dependencies import get_vault_config, get_vault_manager
from app.src.core.exceptions.exception_schemas import ErrorResponse
from app.src.core.exceptions.item_exceptions import ItemNotFoundError
from app.src.domain.entities import TaskItem
from app.src.domain.task_processor import TaskProcessor
from app.src.models.api_models import ProcessingResponse, TaskListResponse, TaskResponse

router = APIRouter()


@router.get(
    "/",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all tasks",
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Vault access failed or filesystem error",
        },
    },
)
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


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific task",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Task not found",
        },
    },
)
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


@router.post(
    "/process-active",
    response_model=ProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Process all active tasks",
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Task processing failed",
        },
    },
)
async def process_active_tasks(
    vault=Depends(get_vault_manager),  # noqa: B008
    config=Depends(get_vault_config),  # noqa: B008
) -> ProcessingResponse:
    processor = TaskProcessor()
    active_tasks = vault.get_notes(config["tasks"], TaskItem)

    for task in active_tasks:
        processor.process_active_task(vault, task, config)

    return ProcessingResponse(
        processed=len(active_tasks),
        message=f"Processed {len(active_tasks)} active tasks",
    )


@router.post(
    "/process-completed",
    response_model=ProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Process all completed tasks",
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Task processing failed",
        },
    },
)
async def process_completed_tasks(
    vault=Depends(get_vault_manager),  # noqa: B008
    config=Depends(get_vault_config),  # noqa: B008
) -> ProcessingResponse:
    processor = TaskProcessor()
    completed_tasks = vault.get_notes(config["completed_tasks"], TaskItem)

    # Get retention setting from config
    retent_for_days = config.get("retent_for_days", 14)

    for task in completed_tasks:
        processor.process_completed_task(vault, task, config, retent_for_days)

    return ProcessingResponse(
        processed=len(completed_tasks),
        message=f"Processed {len(completed_tasks)} completed tasks",
    )
