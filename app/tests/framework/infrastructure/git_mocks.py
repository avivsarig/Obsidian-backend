from contextlib import contextmanager
from typing import Generator
from unittest.mock import MagicMock, patch


@contextmanager
def mock_git_unavailable() -> Generator[None, None, None]:
    def import_side_effect(name, *args, **kwargs):
        if name == "git":
            raise ImportError("git not available")
        return __import__(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=import_side_effect):
        yield


@contextmanager
def mock_git_repo(
    repo_mock: MagicMock | None = None,
) -> Generator[MagicMock, None, None]:
    if repo_mock is None:
        repo_mock = MagicMock()
        repo_mock.head.is_valid.return_value = True

    with patch("git.Repo", return_value=repo_mock):
        yield repo_mock


@contextmanager
def mock_git_repo_error(error: Exception | None = None) -> Generator[None, None, None]:
    if error is None:
        error = Exception("Git repository error")

    with patch("git.Repo", side_effect=error):
        yield
