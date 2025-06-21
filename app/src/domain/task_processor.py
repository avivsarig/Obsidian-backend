import logging
from datetime import datetime

from croniter import croniter

from app.src.domain.date_service import get_date_service
from app.src.domain.entities import ArchiveItem, TaskItem
from app.src.domain.repositories import ArchiveRepository, TaskRepository

logger = logging.getLogger(__name__)


class TaskProcessor:
    def __init__(
        self,
        task_repository: TaskRepository,
        archive_repository: ArchiveRepository,
    ):
        self.task_repository = task_repository
        self.archive_repository = archive_repository

    def process_active_task(
        self,
        task: TaskItem,
        config: dict,
    ) -> TaskItem:
        from app.src.domain.date_service import get_date_service

        logger.info(f"Processing active task: {task.title}")
        date_service = get_date_service()

        if task.done and task.repeat_task:
            logger.info("Task is done and repeating - resetting")
            return self.reset_repeating_task(task, config)

        if task.done and not task.completed_at:
            logger.info("Task is done - filling completion date")
            task.completed_at = datetime.now()

        if task.completed_at and not task.done:
            logger.info("Task not done - clearing completion date")
            task.completed_at = None

        if task.done and task.completed_at:
            logger.info("Task is done - moving to completion cache")
            self.task_repository.move_task(task, config["completed_tasks"])
            return task

        normalized_do_date = date_service.normalize_for_field(task.do_date, "do_date")

        if not normalized_do_date:
            logger.info("No do_date set - setting for today")
            task.do_date = datetime.today()
        elif normalized_do_date.date() < datetime.today().date():
            logger.info("Do date has passed - setting for today")
            task.do_date = datetime.today()
        else:
            task.do_date = normalized_do_date

        self.task_repository.save_task(task, config["tasks"])
        return task

    def reset_repeating_task(
        self,
        task: TaskItem,
        config: dict,
    ) -> TaskItem:
        date_service = get_date_service()
        last_occurrence = self.get_last_occurrence(task)
        next_do_date_str = self.get_next_occurrence(task)

        next_do_date_dt = date_service.parse_datevalue_to_parseddate(next_do_date_str)

        if task.due_date and last_occurrence:
            normalized_due_date = date_service.normalize_for_field(
                task.due_date, "due_date"
            )
            if normalized_due_date:
                grace_period = normalized_due_date - last_occurrence
                task.due_date = next_do_date_dt + grace_period
            else:
                task.due_date = None
        else:
            task.due_date = None

        task.do_date = next_do_date_dt
        task.done = False
        task.completed_at = None

        self.task_repository.save_task(task, config["tasks"])
        return task

    def process_completed_task(
        self,
        task: TaskItem,
        config: dict,
        retent_for_days: int,
    ) -> TaskItem:
        logger.info(f"Processing completed task: {task.title}")

        # if done but no completed_at - update completed_at
        if task.done and not task.completed_at:
            logger.info("No completion date - updating to now")
            task.completed_at = datetime.now()

        # if completed_at but not done - reactivate
        if task.completed_at and not task.done:
            logger.info("Task not done - reactivating")
            task.completed_at = None
            self.task_repository.move_task(task, config["tasks"])
            return task

        # make sure is_project is up to date
        if (task.content == "") == task.is_project:
            logger.info(
                f"Task has {'no' if not task.content else ''} "
                "content - is_project changed to {not task.is_project}"
            )
            task.is_project = not task.is_project

        # is over-retented?
        if (
            task.done
            and isinstance(task.completed_at, datetime)
            and (datetime.now() - task.completed_at).days > retent_for_days
        ):
            logger.info(
                f"Task completed {(datetime.now() - task.completed_at).days} days ago"
            )
            if not task.is_project:
                logger.info("Deleting over-retented task")
                self.task_repository.delete_task(task)
            else:
                self.archive_task(task, config)

        return task

    def archive_task(
        self,
        task: TaskItem,
        config: dict,
    ) -> None:
        logger.info("Archiving task")
        callout = "> [!Example] Task properties"
        for k, v in task.frontmatter.items():
            callout = f"{callout}\n> {k}: {v}"

        content = f"{callout}\n\n{task.content}"

        archive_item = ArchiveItem(
            title=task.title,
            content=content,
            created_at=datetime.now(),
            tags=["Archived-task"],
        )

        self.archive_repository.archive_item(archive_item, config["archive"])
        self.task_repository.delete_task(task)

    def get_last_occurrence(self, task: TaskItem):
        if not task.repeat_task:
            return None
        return croniter(task.repeat_task, datetime.now()).get_prev(datetime)

    def get_next_occurrence(self, task: TaskItem):
        if not task.repeat_task:
            return None
        cron = croniter(task.repeat_task, datetime.now())
        next_timestamp = cron.get_next()
        next_time = datetime.fromtimestamp(next_timestamp)
        return next_time.strftime("%Y-%m-%d")
