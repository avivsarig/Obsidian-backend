from contextlib import contextmanager
from typing import Generator
from unittest.mock import MagicMock, patch

from app.src.application.task_service import TaskApplicationService
from app.src.infrastructure.git.git_manager import GitManager
from app.src.infrastructure.vault_manager import VaultManager


class MockFactory:
    @staticmethod
    @contextmanager
    def mock_services() -> Generator[dict[str, MagicMock], None, None]:
        mocks = {
            "vault_manager": MagicMock(spec=VaultManager),
            "git_manager": MagicMock(spec=GitManager),
            "task_service": MagicMock(spec=TaskApplicationService),
        }

        with (
            patch(
                "app.src.core.dependencies.get_vault_manager",
                return_value=mocks["vault_manager"],
            ),
            patch(
                "app.src.core.dependencies.get_git_manager",
                return_value=mocks["git_manager"],
            ),
            patch(
                "app.src.core.dependencies.get_task_service",
                return_value=mocks["task_service"],
            ),
        ):
            yield mocks

    @staticmethod
    def create_mock_vault_manager() -> MagicMock:
        mock = MagicMock(spec=VaultManager)
        mock.get_notes.return_value = []
        mock.read_note.return_value = None
        mock.write_note.return_value = None
        return mock

    @staticmethod
    def create_mock_task_service() -> MagicMock:
        mock = MagicMock(spec=TaskApplicationService)
        mock.list_tasks.return_value = {
            "tasks": [],
            "total": 0,
            "active": 0,
            "completed": 0,
        }
        return mock
