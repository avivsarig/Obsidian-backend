from functools import lru_cache

from app.src.application.task_service import TaskApplicationService
from app.src.core.config import get_settings
from app.src.domain.task_processor import TaskProcessor
from app.src.infrastructure.git.git_manager import GitManager
from app.src.infrastructure.locking.file_locker import FileLocker
from app.src.infrastructure.repositories import (
    GitRepositoryAdapter,
    VaultArchiveRepository,
    VaultTaskRepository,
)
from app.src.infrastructure.vault_config import get_config
from app.src.infrastructure.vault_manager import VaultManager


@lru_cache
def get_file_locker() -> FileLocker:
    return FileLocker()


@lru_cache
def get_vault_config() -> dict[str, str]:
    config = get_config()
    if not isinstance(config, dict):
        raise TypeError(f"Expected dict from get_config(), got {type(config)}")
    return config


# VaultManager needs singleton behavior for file locking
@lru_cache
def get_vault_manager() -> VaultManager:
    settings = get_settings()

    if settings.vault_path is None:
        raise ValueError(
            "Vault path is not configured. Set VAULT_PATH environment variable"
        )

    file_locker = get_file_locker()
    return VaultManager(
        settings.vault_path,
        file_locker,
    )


@lru_cache
def get_git_manager() -> GitManager | None:
    try:
        settings = get_settings()

        if settings.vault_path is None:
            return None

        git_dir = settings.vault_path / ".git"
        if not git_dir.exists():
            return None

        return GitManager(settings.vault_path)
    except Exception:
        return None


def get_task_repository() -> VaultTaskRepository:
    vault_manager = get_vault_manager()
    return VaultTaskRepository(vault_manager)


def get_archive_repository() -> VaultArchiveRepository:
    vault_manager = get_vault_manager()
    return VaultArchiveRepository(vault_manager)


def get_git_repository() -> GitRepositoryAdapter | None:
    git_manager = get_git_manager()
    return GitRepositoryAdapter(git_manager) if git_manager else None


def get_task_processor() -> TaskProcessor:
    task_repository = get_task_repository()
    archive_repository = get_archive_repository()
    return TaskProcessor(
        task_repository=task_repository,
        archive_repository=archive_repository,
    )


def get_task_service() -> TaskApplicationService:
    task_repository = get_task_repository()
    task_processor = get_task_processor()
    config = get_vault_config()
    git_repository = get_git_repository()

    return TaskApplicationService(
        task_repository=task_repository,
        task_processor=task_processor,
        config=config,
        git_repository=git_repository,
    )
