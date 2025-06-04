from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from app.src.domain.date_parser import TimeParserMixin

StrODate = str | datetime | None


@dataclass
class BaseItem(TimeParserMixin):
    title: str = field(default="", metadata={"internal": True})
    content: str = field(default="", metadata={"internal": True})
    frontmatter: dict = field(default_factory=dict, metadata={"internal": True})
    source_path: Path | None = field(default=None, metadata={"internal": True})

    def __post_init__(self):
        for field_name, field_def in self.__dataclass_fields__.items():
            if (
                not field_def.metadata.get("internal")
                and field_name in self.frontmatter
            ):
                fm_value = self.frontmatter[field_name]
                if field_def.metadata.get("datetime") and isinstance(fm_value, str):
                    setattr(self, field_name, self.parse_str(fm_value))
                else:
                    setattr(self, field_name, fm_value)

    def to_markdown(self, path: Path | str):
        # Sync object attributes back to frontmatter before saving
        for field_name, field_def in self.__dataclass_fields__.items():
            if not field_def.metadata.get("internal"):
                value = getattr(self, field_name, None)
                if value is None:
                    value = ""
                self.frontmatter[field_name] = value

        md = frontmatter.Post(content=self.content, **self.frontmatter)
        path = Path(path)

        with open(path / f"{self.title}.md", "w", encoding="utf-8") as f:
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
    do_date: StrODate = field(default="", metadata={"datetime": True})
    due_date: StrODate = field(default="", metadata={"datetime": True})
    completed_at: StrODate = field(default="", metadata={"datetime": True})
    done: bool = False
    is_high_priority: bool = False
    repeat_task: Optional[str] = field(default="")


@dataclass
class ArchiveItem(BaseItem):
    tags: Optional[list] = None
    created_at: StrODate = field(default="", metadata={"datetime": True})
    URL: str = ""
