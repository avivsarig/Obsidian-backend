from app.src.infrastructure.vault_manager import VaultManager


class TaskService:
    def __init__(
        self,
        vault: VaultManager,
        config: dict,
    ):
        self.vault = vault
        self.config = config
