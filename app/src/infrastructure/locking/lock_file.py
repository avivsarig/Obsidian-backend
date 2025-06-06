import logging
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Generator

from app.src.infrastructure.locking.platform_locks import PlatformLocker

logger = logging.getLogger(__name__)


class LockFile:
    def __init__(
        self,
        target_path: Path,
        platform_locker: PlatformLocker,
    ):
        self.target_path = target_path
        self.lock_path = self._generate_lock_path(target_path)
        self.platform_locker = platform_locker

    @contextmanager
    def acquire(self) -> Generator[None, None, None]:
        self._ensure_lock_directory()

        with open(self.lock_path, "wb") as lock_handle:
            try:
                self.platform_locker.lock_exclusive(lock_handle)
                logger.debug(f"Acquired lock for {self.target_path}")
                yield
            finally:
                self._release_and_cleanup(lock_handle)

    def _generate_lock_path(self, target_path: Path) -> Path:
        return target_path.with_suffix(f"{target_path.suffix}.lock")

    def _ensure_lock_directory(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

    def _release_and_cleanup(self, lock_handle: BinaryIO) -> None:
        try:
            self.platform_locker.unlock(lock_handle)
        except OSError:
            logger.warning(f"Failed to release lock cleanly: {self.lock_path}")

        try:
            self.lock_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(f"Failed to cleanup lock file: {self.lock_path}")
