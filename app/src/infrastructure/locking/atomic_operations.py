import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.src.infrastructure.locking.file_locker import FileLocker


class AtomicFileOperations:
    def __init__(
        self,
        file_locker: FileLocker,
    ):
        self.file_locker = file_locker

    @contextmanager
    def atomic_write(
        self,
        target_path: Path,
    ) -> Generator[Path, None, None]:
        with self.file_locker.acquire_write_lock(target_path):
            temp_path = self._create_temp_file(target_path)

            try:
                yield temp_path
                self._commit_write(
                    temp_path,
                    target_path,
                )
            except Exception:
                self._cleanup_temp_file(temp_path)
                raise

    def _create_temp_file(
        self,
        target_path: Path,
    ) -> Path:
        temp_fd, temp_path_str = tempfile.mkstemp(
            dir=target_path.parent,
            prefix=f".tmp_{target_path.name}_",
        )
        os.close(temp_fd)
        return Path(temp_path_str)

    def _commit_write(
        self,
        temp_path: Path,
        target_path: Path,
    ) -> None:
        temp_path.replace(target_path)

    def _cleanup_temp_file(
        self,
        temp_path: Path,
    ) -> None:
        temp_path.unlink(missing_ok=True)
