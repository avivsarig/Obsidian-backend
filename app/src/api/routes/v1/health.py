import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    vault_status: str
    git_status: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    vault_status = _check_vault_status()
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
        git_status=git_status,
    )


def _check_vault_status() -> str:
    """Check if vault directory is accessible"""
    try:
        vault_path = _get_vault_path()
        return "ok" if vault_path and vault_path.exists() else "error"
    except (OSError, ValueError):
        return "error"


def _check_git_status() -> str:
    """Check git repository status, handling test environments gracefully"""
    try:
        import git

        vault_path = _get_vault_path()
        if not vault_path:
            return "unavailable"

        repo = git.Repo(vault_path)
        return "ok" if not repo.is_dirty() else "dirty"
    except ImportError:
        return "unavailable"
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        return "unavailable"
    except (OSError, ValueError):
        return "error"


def _get_vault_path() -> Optional[Path]:
    """Get vault path, handling different environments"""
    try:
        if os.getenv("TESTING"):
            test_vault = os.getenv("TEST_VAULT_PATH")
            return Path(test_vault) if test_vault else None

        script_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        vault_root = os.path.dirname(script_dir)
        return Path(vault_root)
    except (OSError, ValueError):
        return None
