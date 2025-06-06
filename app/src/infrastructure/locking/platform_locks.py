import contextlib
import fcntl
import platform
from abc import ABC, abstractmethod
from typing import Any, BinaryIO

msvcrt_module: Any = None
with contextlib.suppress(ImportError):
    import msvcrt as msvcrt_module


class PlatformLocker(ABC):
    @abstractmethod
    def lock_exclusive(self, file_handle: BinaryIO) -> None:
        pass

    @abstractmethod
    def unlock(self, file_handle: BinaryIO) -> None:
        pass


class UnixLocker(PlatformLocker):
    def lock_exclusive(self, file_handle: BinaryIO) -> None:
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock(self, file_handle: BinaryIO) -> None:
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


class WindowsLocker(PlatformLocker):
    def __init__(self):
        if msvcrt_module is None:
            raise RuntimeError("msvcrt module not available on this platform")

    def lock_exclusive(self, file_handle: BinaryIO) -> None:
        assert msvcrt_module is not None
        msvcrt_module.locking(file_handle.fileno(), msvcrt_module.LK_NBLCK, 1)

    def unlock(self, file_handle: BinaryIO) -> None:
        assert msvcrt_module is not None
        msvcrt_module.locking(file_handle.fileno(), msvcrt_module.LK_UNLCK, 1)


def get_platform_locker() -> PlatformLocker:
    if platform.system() == "Windows":
        return WindowsLocker()
    return UnixLocker()
