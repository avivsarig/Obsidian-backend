import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import git
from git.exc import GitCommandError

from app.src.core.exceptions.vault_exceptions import VaultGitOperationError

logger = logging.getLogger(__name__)


class GitManager:
    def __init__(self, repository_path: Path):
        self.repo_path = repository_path
        self._repo: git.Repo | None = None
        self._batch_mode = False

    @property
    def repo(self) -> git.Repo:
        if self._repo is None:
            try:
                self._repo = git.Repo(self.repo_path)
            except git.exc.InvalidGitRepositoryError as e:
                raise VaultGitOperationError(
                    message=f"Invalid Git repository at {self.repo_path}",
                    operation="initialize",
                    original_error=e,
                ) from e
        return self._repo

    @property
    def current_branch(self) -> str | None:
        current_branch: str | None = self.repo.active_branch.name
        return current_branch

    def validate_repository_state(self) -> bool:
        try:
            repo = self.repo

            if not repo.head.is_valid():
                logger.warning("Repository has no commits yet")
                return True

            if repo.is_dirty(untracked_files=False):
                logger.warning("Repository has uncommitted changes")

            return True

        except Exception as e:
            logger.error(f"Repository state validation failed: {e}")
            return False

    def pull_latest(self) -> bool:
        try:
            repo = self.repo

            if not repo.remotes:
                logger.debug("No remote configured, skipping pull")
                return True

            if not repo.head.is_valid():
                logger.debug("No commits yet, skipping pull")
                return True

            if repo.is_dirty():
                logger.warning("Cannot pull with uncommitted changes")
                return False

            origin = repo.remotes.origin
            logger.debug("Pulling latest changes from remote")
            origin.pull()
            logger.info("Successfully pulled latest changes")
            return True

        except GitCommandError as e:
            logger.error(f"Failed to pull from remote: {e}")
            return False

    def commit_changes(
        self,
        message: str,
        files: list[Path] | None = None,
    ) -> str | None:
        if self._batch_mode:
            logger.debug(f"Batch mode active - deferring commit: {message}")
            return None

        return self._do_commit(message, files)

    def _do_commit(
        self,
        message: str,
        files: list[Path] | None = None,
    ) -> str | None:
        try:
            repo = self.repo

            if files:
                repo.index.add([str(f.relative_to(self.repo_path)) for f in files])
            else:
                repo.git.add(A=True)

            if not repo.index.diff("HEAD"):
                logger.debug("No changes to commit")
                return None

            commit = repo.index.commit(message)
            commit_hash: str = commit.hexsha
            current_branch = self.current_branch
            logger.info(
                f"Committed changes: {current_branch} - {commit_hash[:8]} - {message}"
            )

            self._push_to_remote()

            return commit_hash

        except GitCommandError as e:
            raise VaultGitOperationError(
                message=f"Failed to commit changes: {message}",
                operation="commit",
                original_error=e,
            ) from e

    def _push_to_remote(self) -> bool:
        try:
            repo = self.repo

            if not repo.remotes:
                logger.debug("No remote configured, skipping push")
                return True

            origin = repo.remotes.origin
            logger.debug("Pushing to remote")
            origin.push()
            logger.info("Successfully pushed to remote")
            return True

        except GitCommandError as e:
            logger.error(f"Failed to push to remote: {e}")
            return False

    @contextmanager
    def batch_sync(
        self, commit_message: str | None = None
    ) -> Generator[None, None, None]:
        if self._batch_mode:
            yield
            return

        if commit_message is None:
            from app.src.domain.date_service import DateService

            commit_message = f"{DateService.now_timestamp_str()}: Batch operation"

        pull_success = self.pull_latest()
        if not pull_success:
            repo = self.repo
            if repo.is_dirty():
                logger.info(
                    "Repository has uncommitted changes, "
                    "proceeding with batch operation"
                )
            elif not repo.remotes:
                logger.info(
                    "No remote configured, proceeding with local batch operation"
                )
            else:
                logger.warning("Failed to pull latest changes, proceeding anyway")

        self._batch_mode = True

        try:
            yield

            commit_hash = self._do_commit(commit_message)
            if commit_hash:
                logger.info(f"Batch operation completed with commit: {commit_hash[:8]}")
            else:
                logger.info("Batch operation completed with no changes")

        except Exception as e:
            logger.error(f"Error during batch operation: {e}")
            raise

        finally:
            self._batch_mode = False

    def force_sync(self) -> bool:
        return self.pull_latest() and self._push_to_remote()
