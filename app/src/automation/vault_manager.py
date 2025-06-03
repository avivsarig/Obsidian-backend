from pathlib import Path

import frontmatter

from app.src.automation.classes import BaseItem


class VaultManager:
    def __init__(
        self,
        vault_path: str | Path,
    ):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

    def read_note(
        self,
        filepath: str | Path,
        item_class: type[BaseItem] = BaseItem,
    ) -> BaseItem:
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
        source_path = item.require_source_path()
        dest_path = Path(destination_dir)

        if not dest_path.is_absolute():
            dest_path = self.vault_path / dest_path

        dest_path = dest_path / source_path.name

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            source_path.replace(dest_path)
            item.source_path = dest_path

        except OSError as e:
            raise RuntimeError(f"Failed to move note: {e}") from e

    def get_notes(
        self,
        folder: str,
        return_item: type[BaseItem] = BaseItem,
    ) -> list[BaseItem]:
        item_path = self.vault_path / folder
        items: list[BaseItem] = []

        for file in item_path.glob("*.md"):
            items.append(self.read_note(file, return_item))

        return items

    def delete_note(
        self,
        item: BaseItem,
    ):
        source_path = item.require_source_path()
        source_path.unlink()
        item.source_path = None

    def write_note(self, item: BaseItem, subfolder: str = "") -> Path:
        output_path = self.vault_path / subfolder
        output_path.mkdir(parents=True, exist_ok=True)

        item.to_markdown(output_path)

        file_path = output_path / f"{item.title}.md"
        item.source_path = file_path

        return file_path

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
