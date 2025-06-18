import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Optional, Tuple

import git

from app.src.core.config import Settings
from app.src.infrastructure.git.git_manager import GitManager
from app.tests.framework.config import test_config
from app.tests.framework.context import TestContext


class TestEnvironmentManager:
    def __init__(self):
        self._active_environments: list[Path] = []
        self._cleanup_handlers: list[Callable[[], None]] = []

    def create_isolated_vault(self, profile_name: str = "unit") -> Path:
        profile = test_config.get_test_profile(profile_name)
        vault_path = profile.vault_path

        vault_path.mkdir(parents=True, exist_ok=True)
        (vault_path / "Tasks").mkdir(exist_ok=True)
        (vault_path / "Tasks" / "Completed").mkdir(exist_ok=True)
        (vault_path / "Knowledge Archive").mkdir(exist_ok=True)

        settings_content = """# Folders
tasks: "Tasks"
completed_tasks: "Tasks/Completed"
archive: "Knowledge Archive"

# Retention
retent_for_days: 14
"""
        settings_file = vault_path / "vault_settings.yaml"
        settings_file.write_text(settings_content)

        self._active_environments.append(vault_path)
        TestContext.set_metadata("vault_path", str(vault_path))
        TestContext.add_trace(f"Created isolated vault: {vault_path}")

        return vault_path

    def setup_git_repository(self, vault_path: Path) -> GitManager:
        repo = git.Repo.init(vault_path)

        repo.index.add(["."])
        repo.index.commit("Initial test vault setup")

        git_manager = GitManager(vault_path)
        TestContext.add_trace(f"Initialized git repository: {vault_path}")

        return git_manager

    def configure_test_settings(self, profile_name: str = "unit") -> Settings:
        profile = test_config.get_test_profile(profile_name)

        overrides = {
            "vault_path": str(profile.vault_path),
            "environment": profile.environment,
            "log_level": profile.log_level,
            "require_auth": profile.require_auth,
            "rate_limit_enabled": profile.rate_limit_enabled,
            "api_keys_str": ",".join(profile.api_keys),
        }

        with test_config.override_settings(**overrides) as settings:
            return settings

    @contextmanager
    def isolated_environment(
        self,
        profile_name: str = "unit",
        with_git: bool = False,
        seed_data: Optional[dict] = None,
    ) -> Generator[Tuple[Path, Settings], None, None]:
        TestContext.new_context(profile=profile_name, with_git=with_git)

        try:
            vault_path = self.create_isolated_vault(profile_name)

            git_manager = None
            if with_git:
                git_manager = self.setup_git_repository(vault_path)
                TestContext.set_metadata("git_manager", git_manager)

            if seed_data:
                self._seed_vault_data(vault_path, seed_data)

            with test_config.override_settings(
                vault_path=str(vault_path),
                environment="test",
                log_level="DEBUG",
                require_auth=False,
                rate_limit_enabled=False,
                api_keys_str="test-key-123",
            ) as settings:
                TestContext.set_metadata("settings", settings)
                yield vault_path, settings

        finally:
            self.cleanup_environment(vault_path)

    def cleanup_environment(self, vault_path: Optional[Path] = None) -> None:
        if vault_path and vault_path in self._active_environments:
            try:
                if vault_path.exists():
                    shutil.rmtree(vault_path, ignore_errors=True)
                self._active_environments.remove(vault_path)
                TestContext.add_trace(f"Cleaned up vault: {vault_path}")
            except Exception as e:
                TestContext.add_trace(f"Cleanup warning: {e}")

    def cleanup_all_environments(self) -> None:
        for vault_path in self._active_environments[:]:
            self.cleanup_environment(vault_path)

        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                TestContext.add_trace(f"Cleanup handler error: {e}")

    def register_cleanup_handler(self, handler: Callable[[], None]) -> None:
        self._cleanup_handlers.append(handler)

    def _seed_vault_data(self, vault_path: Path, seed_data: dict) -> None:
        for folder, files in seed_data.items():
            folder_path = vault_path / folder
            folder_path.mkdir(exist_ok=True)

            for filename, content in files.items():
                file_path = folder_path / f"{filename}.md"
                if isinstance(content, dict):
                    frontmatter = content.get("frontmatter", {})
                    body = content.get("content", "")

                    file_content = "---\n"
                    for key, value in frontmatter.items():
                        file_content += f"{key}: {value}\n"
                    file_content += "---\n\n"
                    file_content += body
                else:
                    file_content = content

                file_path.write_text(file_content)

        TestContext.add_trace(f"Seeded vault with data: {list(seed_data.keys())}")


test_environment = TestEnvironmentManager()
