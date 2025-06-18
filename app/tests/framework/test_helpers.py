import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generator, Optional
from unittest.mock import patch

from app.src.domain.entities import ArchiveItem, TaskItem
from app.tests.framework.context import TestContext


@dataclass
class StateSnapshot:
    vault_files: dict[str, str]
    git_status: dict[str, Any]
    timestamp: float
    metadata: dict[str, Any]


@contextmanager
def freeze_time(target_time: datetime) -> Generator[None, None, None]:
    with (
        patch("app.src.domain.date_service.datetime.now", return_value=target_time),
        patch("datetime.datetime.now", return_value=target_time),
    ):
        TestContext.add_trace(f"Time frozen at: {target_time}")
        yield


def capture_vault_state(vault_path: Path) -> StateSnapshot:
    vault_files = {}

    for file_path in vault_path.rglob("*.md"):
        relative_path = str(file_path.relative_to(vault_path))
        vault_files[relative_path] = file_path.read_text()

    for file_path in vault_path.rglob("*.yaml"):
        relative_path = str(file_path.relative_to(vault_path))
        vault_files[relative_path] = file_path.read_text()

    git_status = {}
    git_dir = vault_path / ".git"
    if git_dir.exists():
        try:
            import git

            repo = git.Repo(vault_path)
            git_status = {
                "current_branch": (
                    repo.active_branch.name if repo.head.is_valid() else None
                ),
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
            }
        except Exception as e:
            git_status = {"error": str(e)}

    snapshot = StateSnapshot(
        vault_files=vault_files,
        git_status=git_status,
        timestamp=time.time(),
        metadata=TestContext.get_current().metadata.copy(),
    )

    TestContext.add_trace(f"Captured vault state: {len(vault_files)} files")
    return snapshot


def restore_vault_state(vault_path: Path, snapshot: StateSnapshot) -> None:
    for file_path in vault_path.rglob("*.md"):
        file_path.unlink()
    for file_path in vault_path.rglob("*.yaml"):
        file_path.unlink()

    for relative_path, content in snapshot.vault_files.items():
        file_path = vault_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    TestContext.add_trace(f"Restored vault state: {len(snapshot.vault_files)} files")


def create_test_task(
    title: str = "Test Task",
    content: str = "Test content",
    is_project: bool = False,
    done: bool = False,
    **kwargs,
) -> TaskItem:
    task = TaskItem(
        title=title, content=content, is_project=is_project, done=done, **kwargs
    )
    TestContext.add_trace(f"Created test task: {title}")
    return task


def create_test_archive(
    title: str = "Test Archive",
    content: str = "Archived content",
    tags: Optional[list[str]] = None,
    **kwargs,
) -> ArchiveItem:
    archive = ArchiveItem(title=title, content=content, tags=tags or ["test"], **kwargs)
    TestContext.add_trace(f"Created test archive: {title}")
    return archive


def count_vault_files(vault_path: Path, pattern: str = "*.md") -> int:
    return len(list(vault_path.rglob(pattern)))


def wait_for_condition(
    condition_func: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1
) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False
