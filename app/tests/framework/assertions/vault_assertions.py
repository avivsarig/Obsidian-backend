from pathlib import Path


class VaultAssertions:
    @staticmethod
    def assert_file_exists(vault_path: Path, relative_path: str) -> None:
        file_path = vault_path / relative_path
        assert file_path.exists(), f"Expected file {relative_path} not found"

    @staticmethod
    def assert_file_not_exists(vault_path: Path, relative_path: str) -> None:
        file_path = vault_path / relative_path
        assert not file_path.exists(), f"File {relative_path} should not exist"

    @staticmethod
    def assert_file_contains(
        vault_path: Path, relative_path: str, content: str
    ) -> None:
        file_path = vault_path / relative_path
        assert file_path.exists(), f"File {relative_path} does not exist"

        actual_content = file_path.read_text()
        assert content in actual_content, (
            f"File {relative_path} does not contain {content!r}\n"
            f"Actual content: {actual_content!r}"
        )

    @staticmethod
    def assert_vault_structure(vault_path: Path) -> None:
        required_dirs = ["Tasks", "Tasks/Completed", "Knowledge Archive"]
        for dir_name in required_dirs:
            dir_path = vault_path / dir_name
            assert dir_path.exists(), f"Required directory {dir_name} missing"
