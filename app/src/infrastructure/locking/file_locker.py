import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.src.core.exceptions.vault_exceptions import VaultConcurrencyError
from app.src.core.util.retrier import Retrier
from app.src.infrastructure.locking.lock_file import LockFile
from app.src.infrastructure.locking.platform_locks import get_platform_locker

logger = logging.getLogger(__name__)


class FileLocker:
    def __init__(
        self,
        timeout_seconds: int = 30,
        max_retries: int = 5,
        base_delay: float = 1,
    ):
        self.timeout_seconds = timeout_seconds
        self.platform_locker = get_platform_locker()
        self.retrier = Retrier(max_retries, base_delay)

    @contextmanager
    def acquire_write_lock(
        self,
        file_path: Path,
    ) -> Generator[None, None, None]:
        lock_file = LockFile(
            file_path,
            self.platform_locker,
        )

        try:
            with self.retrier.execute(lambda: lock_file.acquire()):
                yield
        except Exception as e:
            raise VaultConcurrencyError(
                message=f"Failed to acquire write lock for {file_path}",
                resource=str(file_path),
                timeout_seconds=self.timeout_seconds,
            ) from e

    @contextmanager
    def acquire_read_lock(
        self,
        file_path: Path,
    ) -> Generator[None, None, None]:
        logger.debug(f"Acquired read lock for {file_path}")
        yield
