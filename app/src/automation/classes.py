from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from helper import TimeParserMixin

import frontmatter

StrODate = str | datetime | None


@dataclass
class BaseItem(TimeParserMixin):
    title: str = field(default="", metadata={"internal": True})
    content: str = field(default="", metadata={"internal": True})
    frontmatter: dict = field(default_factory=dict, metadata={"internal": True})
    source_path: Path | None = field(default_factory=Path, metadata={"internal": True})

    def __post_init__(self):
        for name, field in self.__dataclass_fields__.items():
            if not field.metadata.get("internal") and name in self.frontmatter:
                fm_value = self.frontmatter[name]
                if field.metadata.get("datetime") and type(fm_value) == str:
                    setattr(self, name, self.parse_str(fm_value))
                else:
                    setattr(self, name, fm_value)

    def to_markdown(self, path: Path | str):
        # ensure fm updated before saving
        for name, field in self.__dataclass_fields__.items():
            if not field.metadata.get("internal"):
                value = getattr(self, name, None)

                if value is None:
                    value = ""

                self.frontmatter[name] = value

        md = frontmatter.Post(content=self.content, **self.frontmatter)
        path = Path(path)

        with open(path / f"{self.title}.md", "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(md))


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
