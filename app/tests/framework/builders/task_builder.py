from dataclasses import replace
from datetime import datetime

from app.src.domain.entities import TaskItem


class TaskBuilder:
    def __init__(self, base: TaskItem | None = None):
        self._task = base or TaskItem(
            title="Test Task", content="Test content", is_project=False, done=False
        )

    def with_title(self, title: str) -> "TaskBuilder":
        return TaskBuilder(replace(self._task, title=title))

    def with_content(self, content: str) -> "TaskBuilder":
        return TaskBuilder(replace(self._task, content=content))

    def as_project(self) -> "TaskBuilder":
        return TaskBuilder(replace(self._task, is_project=True))

    def as_completed(self, completed_at: datetime | None = None) -> "TaskBuilder":
        return TaskBuilder(
            replace(self._task, done=True, completed_at=completed_at or datetime.now())
        )

    def with_due_date(self, due_date: str) -> "TaskBuilder":
        return TaskBuilder(replace(self._task, due_date=due_date))

    def with_repeat(self, cron_expr: str) -> "TaskBuilder":
        return TaskBuilder(replace(self._task, repeat_task=cron_expr))

    def build(self) -> TaskItem:
        return self._task
