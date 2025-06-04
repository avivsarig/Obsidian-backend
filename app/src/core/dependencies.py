from functools import lru_cache

from app.src.core.config import get_settings
from app.src.infrastructure.vault_config import get_config
from app.src.infrastructure.vault_manager import VaultManager


@lru_cache
def get_vault_manager() -> VaultManager:
    settings = get_settings()

    if settings.vault_path is None:
        raise ValueError(
            "Vault path is not configured. Set VAULT_PATH environment variable"
        )

    return VaultManager(settings.vault_path)


@lru_cache
def get_vault_config() -> dict[str, str]:
    config = get_config()
    if not isinstance(config, dict):
        raise TypeError(f"Expected dict from get_config(), got {type(config)}")

    return config
