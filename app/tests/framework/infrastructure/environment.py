import contextlib
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Protocol

from app.src.core.config import Settings


class VaultEnvironment(Protocol):
    vault_path: Path
    settings: Settings

    def cleanup(self) -> None:
        ...


class IsolatedVaultEnvironment:
    def __init__(
        self,
        vault_path: Path,
        settings: Settings,
    ):
        self.vault_path = vault_path
        self.settings = settings
        self._cleanup_handlers: list[Callable[[], None]] = []

    def add_cleanup(self, handler: Callable[[], None]) -> None:
        self._cleanup_handlers.append(handler)

    def cleanup(self) -> None:
        for handler in reversed(self._cleanup_handlers):
            with contextlib.suppress(Exception):
                handler()


class EnvironmentFactory:
    @staticmethod
    @contextmanager
    def create_isolated(
        profile: str = "unit",
    ) -> Generator[VaultEnvironment, None, None]:
        vault_path = Path(tempfile.mkdtemp(prefix=f"vault-{profile}-"))

        # Setup vault structure
        (vault_path / "Tasks").mkdir()
        (vault_path / "Tasks" / "Completed").mkdir()
        (vault_path / "Knowledge Archive").mkdir()

        settings = Settings(
            vault_path=vault_path,
            environment="test",
            require_auth=False,
            rate_limit_enabled=False,
        )

        env = IsolatedVaultEnvironment(vault_path, settings)
        env.add_cleanup(lambda: shutil.rmtree(vault_path, ignore_errors=True))

        try:
            yield env
        finally:
            env.cleanup()
