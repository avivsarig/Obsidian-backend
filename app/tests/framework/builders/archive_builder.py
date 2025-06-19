from dataclasses import replace
from datetime import datetime

from app.src.domain.entities import ArchiveItem


class ArchiveBuilder:
    def __init__(self, base: ArchiveItem | None = None):
        self._archive = base or ArchiveItem(
            title="Test Archive",
            content="Test archive content",
            tags=["test"],
            created_at=datetime.now(),
        )

    def with_title(self, title: str) -> "ArchiveBuilder":
        return ArchiveBuilder(replace(self._archive, title=title))

    def with_content(self, content: str) -> "ArchiveBuilder":
        return ArchiveBuilder(replace(self._archive, content=content))

    def with_tags(self, tags: list[str]) -> "ArchiveBuilder":
        return ArchiveBuilder(replace(self._archive, tags=tags))

    def with_url(self, url: str) -> "ArchiveBuilder":
        return ArchiveBuilder(replace(self._archive, URL=url))

    def created_at(self, timestamp: datetime) -> "ArchiveBuilder":
        return ArchiveBuilder(replace(self._archive, created_at=timestamp))

    def build(self) -> ArchiveItem:
        return self._archive
