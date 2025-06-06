import logging
from pathlib import Path

import frontmatter

from app.src.core.exceptions.vault_exceptions import VaultFileOperationError
from app.src.domain.entities import BaseItem
from app.src.infrastructure.locking.atomic_operations import AtomicFileOperations
from app.src.infrastructure.locking.file_locker import FileLocker

logger = logging.getLogger(__name__)


class VaultManager:
    def __init__(
        self,
        vault_path: str | Path,
        file_locker: FileLocker | None = None,
    ):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

        self.file_locker = file_locker or FileLocker()
        self.atomic_ops = AtomicFileOperations(self.file_locker)

    def read_note(
        self,
        filepath: str | Path,
        item_class: type[BaseItem] = BaseItem,
    ) -> BaseItem:
        path = Path(filepath)

        with self.file_locker.acquire_read_lock(path):
            post = self._atomic_read_note(path)

        return item_class(
            title=path.stem,
            content=post.content,
            frontmatter=post.metadata,
            source_path=path,
        )

    def _atomic_read_note(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Note not found: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                post = frontmatter.load(f)
                return post

        except OSError as e:
            raise VaultFileOperationError(
                operation="read",
                path=str(path),
                original_error=e,
            ) from e

    def write_note(
        self,
        item: BaseItem,
        target_dir: str = "",
    ) -> Path:
        output_path = self.vault_path / target_dir
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{item.title}.md"

        self._atomic_write_note(
            file_path=file_path,
            item=item,
        )

        return file_path

    def _atomic_write_note(
        self,
        file_path: Path,
        item: BaseItem,
    ) -> None:
        try:
            with self.atomic_ops.atomic_write(file_path) as temp_path:
                self._write_item_to_file(item, temp_path)

            item.source_path = file_path
            logger.info(f"Successfully wrote note: {file_path}")

        except Exception as e:
            raise VaultFileOperationError(
                operation="write",
                path=str(file_path),
                original_error=e,
            ) from e

    def _write_item_to_file(self, item: BaseItem, path: Path):
        md = frontmatter.Post(content=item.content, **item.frontmatter)
        file_path = path / f"{item.title}.md"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(md))

    def move_note(
        self,
        item: BaseItem,
        destination_dir: str | Path,
    ):
        source_path = item.require_source_path()
        dest_path = self._resolve_destination_path(
            destination_dir,
            source_path,
        )

        if source_path == dest_path:
            return

        try:
            self._atomic_move_note(source_path, dest_path)
            item.source_path = dest_path
            logger.info(f"Moved note: {source_path} -> {dest_path}")

        except OSError as e:
            raise VaultFileOperationError(
                operation="move",
                path=f"{source_path} -> {dest_path}",
                original_error=e,
            ) from e

    def _atomic_move_note(
        self,
        source_path: Path,
        dest_path: Path,
    ) -> None:
        # sort to prevent deadlocks
        paths_to_lock = sorted([source_path, dest_path], key=str)

        # with self.file_locker.acquire_write_lock(paths_to_lock[0]):
        #     with self.file_locker.acquire_write_lock(paths_to_lock[1]):
        #         source_path.replace(dest_path)

        with (
            self.file_locker.acquire_write_lock(paths_to_lock[0]),
            self.file_locker.acquire_write_lock(paths_to_lock[1]),
        ):
            source_path.replace(dest_path)

    def _resolve_destination_path(
        self,
        destination_dir: str | Path,
        source_path: Path,
    ) -> Path:
        dest_path = Path(destination_dir)
        if not dest_path.is_absolute():
            dest_path = self.vault_path / dest_path

        dest_path.mkdir(parents=True, exist_ok=True)
        return dest_path / source_path.name

    def get_notes(
        self,
        folder: str,
        return_item: type[BaseItem] = BaseItem,
    ) -> list[BaseItem]:
        item_path = self.vault_path / folder
        items: list[BaseItem] = []

        for file in item_path.glob("*.md"):
            try:
                items.append(self.read_note(file, return_item))
            except (FileNotFoundError, VaultFileOperationError) as e:
                logger.warning(f"Skipping problematic file {file}: {e}")
                continue

        return items

    def delete_note(
        self,
        item: BaseItem,
    ):
        file_path = item.require_source_path()
        self._atomic_delete_note(item=item, file_path=file_path)
        logger.info(f"Deleted note: {file_path}")

    def _atomic_delete_note(self, item, file_path):
        try:
            with self.file_locker.acquire_write_lock(file_path):
                file_path.unlink()
                item.source_path = None

        except OSError as e:
            raise VaultFileOperationError(
                operation="delete",
                path=str(file_path),
                original_error=e,
            ) from e

    # def find_notes(self, pattern: str = "*.md") -> List[Path]:
    #     """Find all notes matching the pattern"""
    #     return list(self.vault_path.rglob(pattern))

    # def read_archives(self, folder: str = "archive") -> List[ArchiveItem]:
    #     """Read all archive items from a specific folder"""
    #     archive_path = self.vault_path / folder
    #     archives = []

    #     for file in archive_path.glob("*.md"):
    #         archives.append(self.read_note(file, ArchiveItem))

    #     return archives
