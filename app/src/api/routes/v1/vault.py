from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.src.core.dependencies import get_git_manager
from app.src.core.exceptions.exception_schemas import ErrorResponse
from app.src.infrastructure.git.git_manager import GitManager

router = APIRouter()


class GitPullResponse(BaseModel):
    success: bool
    message: str
    current_branch: str | None = None
    repository_valid: bool


@router.post(
    "/pull",
    response_model=GitPullResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull latest changes from remote repository",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Git repository not configured or not available",
        },
        500: {
            "model": ErrorResponse,
            "description": "Git operation failed",
        },
    },
)
async def pull_latest_changes(
    git_manager: GitManager | None = Depends(get_git_manager),  # noqa: B008
) -> GitPullResponse:
    if git_manager is None:
        raise HTTPException(
            status_code=404,
            detail="Git repository not configured or not available",
        )

    repository_valid = git_manager.validate_repository_state()
    current_branch = git_manager.current_branch

    if not repository_valid:
        return GitPullResponse(
            success=False,
            message="Repository state validation failed",
            current_branch=current_branch,
            repository_valid=False,
        )

    pull_success = git_manager.pull_latest()

    if pull_success:
        return GitPullResponse(
            success=True,
            message="Successfully pulled latest changes",
            current_branch=current_branch,
            repository_valid=True,
        )
    else:
        return GitPullResponse(
            success=False,
            message="Failed to pull changes - "
            "check repository state and remote connectivity",
            current_branch=current_branch,
            repository_valid=True,
        )
