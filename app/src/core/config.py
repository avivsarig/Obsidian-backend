import os
import tempfile
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # TODO: check if need to remove?
    api_key: str = "dev-key-change-in-production"
    api_keys_str: str = Field(default="", alias="API_KEYS")
    aws_secrets_manager_key_name: str = ""
    require_auth: bool = True

    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100

    allowed_origins: list[str] = ["http://localhost:3000"]

    vault_path: Path | None = None
    git_repo_url: str = ""

    port: int = 8000

    @property
    def api_keys(self) -> list[str]:
        if not self.api_keys_str:
            return []
        return [key.strip() for key in self.api_keys_str.split(",") if key.strip()]

    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.vault_path:
            self.vault_path = self._discover_vault_path()

    @property
    def host(self) -> str:
        if self.environment == "production":
            # Required for container networking
            return "0.0.0.0"  # nosec B104 # noqa: S104
        return "127.0.0.1"

    def _get_test_vault_path(self) -> Path:
        if custom_path := os.getenv("TEST_VAULT_PATH"):
            return Path(custom_path)
        return Path(tempfile.mkdtemp(prefix="vault-test-", suffix="secure"))

    def _discover_vault_path(self) -> Path:
        if os.getenv("TESTING"):
            return self._get_test_vault_path()

        if self.environment == "production":
            return Path("/opt/vault")

        if vault_env := os.getenv("VAULT_PATH"):
            return Path(vault_env)

        current = Path(__file__).parent
        while current != current.parent:
            if (current / "pyproject.toml").exists() or (current / ".git").exists():
                vault_path = current.parent / "vault"
                if vault_path.exists():
                    return vault_path
                break
            current = current.parent

        raise ValueError("Vault not found. Set VAULT_PATH environment variable.")


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
