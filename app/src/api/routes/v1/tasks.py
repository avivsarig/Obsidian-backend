from fastapi import APIRouter, Depends

from app.src.automation.classes import TaskItem
from app.src.core.dependencies import get_vault_config, get_vault_manager

router = APIRouter()


@router.get("/")
async def list_tasks(
    vault=Depends(get_vault_manager),  # noqa: B008
    config=Depends(get_vault_config),  # noqa: B008
) -> list[TaskItem]:
    active_tasks: list[TaskItem] = vault.get_notes(
        config["tasks"],
        TaskItem,
    )
    completed_tasks: list[TaskItem] = vault.get_notes(
        config["completed_tasks"],
        TaskItem,
    )
    tasks: list[TaskItem] = active_tasks + completed_tasks

    return tasks
