from pydantic import BaseModel, Field

from app.src.domain.entities import TaskItem


class TaskResponse(BaseModel):
    title: str = Field(..., description="Task title")
    content: str = Field(..., description="Task content/description")
    is_project: bool = Field(..., description="Whether this is a project")
    do_date: str | None = Field(None, description="When to do this task (YYYY-MM-DD)")
    due_date: str | None = Field(None, description="When this task is due (YYYY-MM-DD)")
    completed_at: str | None = Field(None, description="When task was completed")
    done: bool = Field(..., description="Whether task is completed")
    is_high_priority: bool = Field(..., description="Whether task is high priority")
    repeat_task: str | None = Field(
        None, description="Cron expression for recurring tasks"
    )

    @classmethod
    def from_task_item(cls, task: TaskItem) -> "TaskResponse":
        return cls(
            title=task.title,
            content=task.content,
            is_project=task.is_project,
            do_date=str(task.do_date) if task.do_date else None,
            due_date=str(task.due_date) if task.due_date else None,
            completed_at=str(task.completed_at) if task.completed_at else None,
            done=task.done,
            is_high_priority=task.is_high_priority,
            repeat_task=task.repeat_task,
        )


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int = Field(..., description="Total number of tasks")
    active: int = Field(..., description="Number of active tasks")
    completed: int = Field(..., description="Number of completed tasks")


class ProcessingResponse(BaseModel):
    processed: int = Field(..., description="Number of tasks processed")
    message: str = Field(..., description="Summary of processing results")
