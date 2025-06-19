from app.tests.framework.infrastructure.environment import VaultEnvironment


class VaultBuilder:
    def __init__(self, environment: VaultEnvironment):
        self._env = environment
        self._tasks: dict[str, dict] = {}
        self._completed: dict[str, dict] = {}
        self._archives: dict[str, dict] = {}

    def with_task(self, name: str, **frontmatter) -> "VaultBuilder":
        self._tasks[name] = {
            "frontmatter": frontmatter,
            "content": frontmatter.pop("content", ""),
        }
        return self

    def with_completed_task(self, name: str, **frontmatter) -> "VaultBuilder":
        self._completed[name] = {
            "frontmatter": frontmatter,
            "content": frontmatter.pop("content", ""),
        }
        return self

    def with_archive(
        self, name: str, content: str = "", **frontmatter
    ) -> "VaultBuilder":
        self._archives[name] = {"frontmatter": frontmatter, "content": content}
        return self

    def build(self) -> VaultEnvironment:
        self._write_files("Tasks", self._tasks)
        self._write_files("Tasks/Completed", self._completed)
        self._write_files("Knowledge Archive", self._archives)
        return self._env

    def _write_files(self, folder: str, files: dict[str, dict]) -> None:
        folder_path = self._env.vault_path / folder
        folder_path.mkdir(exist_ok=True)

        for name, data in files.items():
            file_path = folder_path / f"{name}.md"
            content = self._format_file_content(data["frontmatter"], data["content"])
            file_path.write_text(content)

    def _format_file_content(self, frontmatter: dict, content: str) -> str:
        if not frontmatter:
            return content

        fm_lines = ["---"]
        for key, value in frontmatter.items():
            fm_lines.append(f"{key}: {value}")
        fm_lines.extend(["---", "", content])
        return "\n".join(fm_lines)
