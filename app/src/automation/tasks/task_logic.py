import logging
from croniter import croniter
from datetime import datetime

from classes import TaskItem, ArchiveItem
from logger import LoggingMixin
from vault_manager import VaultManager


class TaskProcessor(LoggingMixin):
    def process_active_task(self, vault: VaultManager, task: TaskItem, config):
        self.logger.info(f"Processing active task: {task.title}")
        if task.done and task.repeat_task:
            self.logger.info("Task is done and repeating - resetting")
            self.reset_repeating_task(
                task=task,
                vault=vault,
                config=config,
            )
            return

        # if done - update completed_at
        if task.done and not task.completed_at:
            self.logger.info("Task is done - filling completion date")
            task.completed_at = datetime.now()

        # if completed_at but not done - clear completed_at
        if task.completed_at and not task.done:
            self.logger.info("Task not done - clearing completion date")
            task.completed_at = None

        # if done and has completed_at - move to completed tasks dir
        if task.done and task.completed_at:
            self.logger.info("Task is done - moving to completion cache")
            vault.move_note(item=task, destination_dir=config["completed_tasks"])

        # is do_date expired?
        # TODO: datetime is invalid for some reason, e.g.: do_date = 2025-04-01, of type <class 'datetime.date'>
        if not isinstance(task.do_date, datetime):
            self.logger.info("Do date is invalid - setting for today")
            self.logger.info(f"do_date = {task.do_date}, of type {type(task.do_date)}")
            task.do_date = datetime.today().strftime("%Y-%m-%d")
        elif (task.do_date.date() - datetime.today().date()).days < 0:
            self.logger.info("Do date have passed - setting for today")
            task.do_date = datetime.today().strftime("%Y-%m-%d")

        vault.write_note(task, subfolder=config["tasks"])

    def process_completed_task(
        self,
        vault: VaultManager,
        task: TaskItem,
        config,
        retent_for_days,
    ):
        self.logger.info(f"Processing completed task: {task.title}")

        # if done but no completed_at - update completed_at
        if task.done and not task.completed_at:
            self.logger.info("No completion date - updating to now")
            task.completed_at = datetime.now()

        # if completed_at but not done - reactivate
        if task.completed_at and not task.done:
            self.logger.info("Task not done - reactivating")
            task.completed_at = None
            vault.move_note(item=task, destination_dir=config["tasks"])

        # make sure is_project is up to date
        if (task.content == "") == task.is_project:
            self.logger.info(
                f"Task has {'no' if not task.content else ''} content - is_project changed to {not task.is_project}"
            )
            task.is_project = not task.is_project

        # is over-retented?
        if (
            task.done
            and isinstance(task.completed_at, datetime)
            and (datetime.now() - task.completed_at).days > retent_for_days
        ):
            self.logger.info(
                f"Task completed {(datetime.now() - task.completed_at).days} days ago"
            )
            if not task.is_project:
                self.logger.info(f"Deleting over-retented task")
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
        self.logger.info("Archiving task")
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
        return (
            croniter(task.repeat_task, datetime.now())
            .get_next(datetime)
            .strftime("%Y-%m-%d")
        )

    def reset_repeating_task(
        self,
        task: TaskItem,
        vault: VaultManager,
        config,
    ):
        last_occurrence = self.get_last_occurrence(task)
        next_do_date = self.get_next_occurrence(task)

        if task.due_date and last_occurrence:
            grace_period = task.due_date - last_occurrence
            task.due_date = next_do_date + grace_period
        else:
            task.due_date = None

        task.do_date = next_do_date
        task.done = False
        task.completed_at = None

        vault.write_note(task, subfolder=config["tasks"])
