from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch


class ErrorScenarios:
    @staticmethod
    @contextmanager
    def vault_permission_error() -> Generator[None, None, None]:
        with patch(
            "pathlib.Path.write_text", side_effect=PermissionError("Access denied")
        ):
            yield

    @staticmethod
    @contextmanager
    def disk_full_error() -> Generator[None, None, None]:
        with patch(
            "pathlib.Path.write_text", side_effect=OSError("No space left on device")
        ):
            yield

    @staticmethod
    @contextmanager
    def git_operation_error() -> Generator[None, None, None]:
        with patch("git.Repo.index") as mock_index:
            mock_index.commit.side_effect = Exception("Git operation failed")
            yield

    @staticmethod
    @contextmanager
    def network_timeout() -> Generator[None, None, None]:
        with patch("requests.get", side_effect=TimeoutError("Network timeout")):
            yield
