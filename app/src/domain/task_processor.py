import logging
from datetime import datetime

from croniter import croniter

from app.src.domain.entities import ArchiveItem, TaskItem
from app.src.infrastructure.vault_manager import VaultManager

logger = logging.getLogger(__name__)


class TaskProcessor:
    def process_active_task(
        self,
        vault: VaultManager,
        task: TaskItem,
        config,
    ):
        logger.info(f"Processing active task: {task.title}")
        if task.done and task.repeat_task:
            logger.info("Task is done and repeating - resetting")
            self.reset_repeating_task(
                task=task,
                vault=vault,
                config=config,
            )
            return

        # if done - update completed_at
        if task.done and not task.completed_at:
            logger.info("Task is done - filling completion date")
            task.completed_at = datetime.now()

        # if completed_at but not done - clear completed_at
        if task.completed_at and not task.done:
            logger.info("Task not done - clearing completion date")
            task.completed_at = None

        # if done and has completed_at - move to completed tasks dir
        if task.done and task.completed_at:
            logger.info("Task is done - moving to completion cache")
            vault.move_note(item=task, destination_dir=config["completed_tasks"])

        # is do_date expired?
        # TODO: datetime is invalid for some reason
        # e.g.: do_date = 2025-04-01, of type <class 'datetime.date'>
        if not isinstance(task.do_date, datetime):
            logger.info("Do date is invalid - setting for today")
            logger.info(f"do_date = {task.do_date}, of type {type(task.do_date)}")
            task.do_date = datetime.today().strftime("%Y-%m-%d")
        elif (task.do_date.date() - datetime.today().date()).days < 0:
            logger.info("Do date have passed - setting for today")
            task.do_date = datetime.today().strftime("%Y-%m-%d")

        vault.write_note(task, subfolder=config["tasks"])

    def process_completed_task(
        self,
        vault: VaultManager,
        task: TaskItem,
        config,
        retent_for_days,
    ):
        logger.info(f"Processing completed task: {task.title}")

        # if done but no completed_at - update completed_at
        if task.done and not task.completed_at:
            logger.info("No completion date - updating to now")
            task.completed_at = datetime.now()

        # if completed_at but not done - reactivate
        if task.completed_at and not task.done:
            logger.info("Task not done - reactivating")
            task.completed_at = None
            vault.move_note(item=task, destination_dir=config["tasks"])

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
                vault.delete_note(task)
            else:
                self.archive_task(
                    vault=vault,
                    task=task,
                    config=config,
                )

    def archive_task(
        self,
        vault: VaultManager,
        task: TaskItem,
        config,
    ):
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

        vault.write_note(item=archive_item, subfolder=config["archive"])
        vault.delete_note(task)

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

    def reset_repeating_task(
        self,
        task: TaskItem,
        vault: VaultManager,
        config,
    ):
        last_occurrence = self.get_last_occurrence(task)
        next_do_date_str = self.get_next_occurrence(task)
        next_do_date_dt = datetime.strptime(next_do_date_str, "%Y-%m-%d")

        if task.due_date and last_occurrence:
            grace_period = task.due_date - last_occurrence
            task.due_date = (next_do_date_dt + grace_period).strftime("%Y-%m-%d")
        else:
            task.due_date = None

        task.do_date = next_do_date_str
        task.done = False
        task.completed_at = None

        vault.write_note(task, subfolder=config["tasks"])
