from functools import lru_cache

from app.src.core.config import get_settings
from app.src.domain.task_processor import TaskProcessor
from app.src.infrastructure.locking.file_locker import FileLocker
from app.src.infrastructure.vault_config import get_config
from app.src.infrastructure.vault_manager import VaultManager
from app.src.services.task_service import TaskService


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


def get_task_processor() -> TaskProcessor:
    return TaskProcessor()


def get_task_service() -> TaskService:
    vault_manager = get_vault_manager()
    task_processor = get_task_processor()
    config = get_vault_config()

    return TaskService(
        vault_manager=vault_manager,
        task_processor=task_processor,
        config=config,
    )
