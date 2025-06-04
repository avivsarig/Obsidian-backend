from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from app.src.domain.date_service import get_date_service
from app.src.domain.value_objects import DateValue


@dataclass
class BaseItem:
    title: str = field(default="", metadata={"internal": True})
    content: str = field(default="", metadata={"internal": True})
    frontmatter: dict = field(default_factory=dict, metadata={"internal": True})
    source_path: Path | None = field(default=None, metadata={"internal": True})

    def __post_init__(self):
        self._sync_from_frontmatter()

    def to_markdown(self, path: Path | str):
        self._sync_to_frontmatter()
        self._write_markdown_file(Path(path))

    def _sync_from_frontmatter(self):
        date_service = get_date_service()

        for field_name, field_def in self._get_data_fields():
            if field_name in self.frontmatter:
                fm_value = self.frontmatter[field_name]

                if field_def.metadata.get("datetime"):
                    value = date_service.normalize_for_field(fm_value, field_name)
                else:
                    value = fm_value

                setattr(self, field_name, value)

    def _sync_to_frontmatter(self):
        date_service = get_date_service()

        for field_name, field_def in self._get_data_fields():
            value = getattr(self, field_name, None)

            if field_def.metadata.get("datetime") and value is not None:
                value = date_service.format_for_storage(value, field_name)
            elif value is None:
                value = ""

            self.frontmatter[field_name] = value

    def _get_data_fields(self):
        return [
            (name, field_def)
            for name, field_def in self.__dataclass_fields__.items()
            if not field_def.metadata.get("internal")
        ]

    def _write_markdown_file(self, path: Path):
        md = frontmatter.Post(content=self.content, **self.frontmatter)
        file_path = path / f"{self.title}.md"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(md))

    @property
    def is_persisted(self) -> bool:
        return self.source_path is not None and self.source_path.exists()

    def require_source_path(self) -> Path:
        if self.source_path is None:
            raise ValueError(
                f"Item '{self.title}' has no source file path. "
                "This operation requires the item to be saved first."
            )
        return self.source_path


@dataclass
class TaskItem(BaseItem):
    is_project: bool = False
    do_date: DateValue = field(default="", metadata={"datetime": True})
    due_date: DateValue = field(default="", metadata={"datetime": True})
    completed_at: DateValue = field(default="", metadata={"datetime": True})
    done: bool = False
    is_high_priority: bool = False
    repeat_task: str | None = field(default="")


@dataclass
class ArchiveItem(BaseItem):
    tags: list | None = None
    created_at: DateValue = field(default="", metadata={"datetime": True})
    URL: str = ""
