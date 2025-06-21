import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.src.application.task_service import TaskApplicationService
from app.src.core.dependencies import get_task_service
from app.src.core.exceptions.exception_schemas import ErrorResponse
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
    task_service: TaskApplicationService = Depends(get_task_service),  # noqa: B008
) -> TaskListResponse:
    return task_service.list_tasks(include_completed=include_completed)


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
    task_service: TaskApplicationService = Depends(get_task_service),  # noqa B008
) -> TaskResponse:
    decoded_task_id = urllib.parse.unquote(task_id)
    return task_service.get_task_by_id(decoded_task_id)


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
    task_service: TaskApplicationService = Depends(get_task_service),  # noqa: B008
) -> ProcessingResponse:
    return task_service.process_active_tasks()


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
    task_service: TaskApplicationService = Depends(get_task_service),  # noqa: B008
) -> ProcessingResponse:
    return task_service.process_completed_tasks()
