from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.src.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    vault_status: str
    vault_file_count: int
    git_status: str


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    """Basic health check endpoint"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    vault_status, file_count = _check_vault_status_and_file_count()
    git_status = _check_git_status()

    overall_status = (
        "ok"
        if vault_status == "ok" and git_status in ["ok", "unavailable"]
        else "error"
    )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        vault_status=vault_status,
        vault_file_count=file_count,
        git_status=git_status,
    )


def _check_vault_status_and_file_count() -> tuple[str, int]:
    try:
        settings = get_settings()
        vault_path = settings.vault_path

        if not vault_path or not vault_path.exists():
            return "error", 0

        file_count = _count_files_recursive(vault_path)
        return "ok", file_count
    except (OSError, ValueError):
        return "error", 0


def _count_files_recursive(path: Path) -> int:
    try:
        count = 0
        for item in path.iterdir():
            try:
                if item.is_file():
                    count += 1
                elif item.is_dir() and not item.is_symlink():
                    count += _count_files_recursive(item)
            except OSError:
                continue
        return count
    except OSError:
        return 0


def _check_git_status() -> str:
    try:
        import git

        settings = get_settings()
        vault_path = settings.vault_path

        if not vault_path:
            return "unavailable"

        repo = git.Repo(vault_path)
        return "ok" if repo.head.is_valid() else "error"
    except Exception:
        return "unavailable"
