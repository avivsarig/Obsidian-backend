from pathlib import Path

import frontmatter
from classes import BaseItem


class VaultManager:
    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def read_note(
        self,
        filepath: str | Path,
        item_class: type[BaseItem] = BaseItem,
    ) -> BaseItem:
        """Read a single note and return it as an item object"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Note not found: {filepath}")

        with open(path, encoding="utf-8") as f:
            post = frontmatter.load(f)

        return item_class(
            title=path.stem,
            content=post.content,
            frontmatter=post.metadata,
            source_path=path,
        )

    def move_note(
        self,
        item: BaseItem,
        destination_dir: str | Path,
    ):
        """Move a note to a new location within the vault"""

        dest_path = Path(destination_dir)

        if not dest_path.is_absolute():
            dest_path = self.vault_path / dest_path

        dest_path = dest_path / item.source_path.name

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            item.source_path.replace(dest_path)
            item.source_path = dest_path

        except OSError as e:
            raise RuntimeError(f"Failed to move note: {e}") from e

    def get_notes(
        self,
        folder: str,
        return_item: type[BaseItem] = BaseItem,
    ):
        """Read all notes from a specific folder"""

        item_path = self.vault_path / folder
        items = []

        for file in item_path.glob("*.md"):
            items.append(self.read_note(file, return_item))

        return items

    def delete_note(
        self,
        item: BaseItem,
    ):
        """Delete items file"""
        if item.source_path:
            item.source_path.unlink()
            item.source_path = None

    def write_note(self, item: BaseItem, subfolder: str = "") -> Path:
        """Write an item to the vault"""
        output_path = self.vault_path / subfolder
        output_path.mkdir(parents=True, exist_ok=True)

        item.to_markdown(output_path)
        return output_path / f"{item.title}.md"

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
