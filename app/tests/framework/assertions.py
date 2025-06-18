from pathlib import Path

from app.src.domain.entities import ArchiveItem, TaskItem


def assert_task_equal(actual: TaskItem, expected: TaskItem) -> None:
    errors = []

    if actual.title != expected.title:
        errors.append(f"Title: got '{actual.title}', expected '{expected.title}'")

    if actual.content != expected.content:
        errors.append(f"Content: got '{actual.content}', expected '{expected.content}'")

    if actual.is_project != expected.is_project:
        errors.append(
            f"is_project: got {actual.is_project}, expected {expected.is_project}"
        )

    if actual.done != expected.done:
        errors.append(f"done: got {actual.done}, expected {expected.done}")

    if actual.is_high_priority != expected.is_high_priority:
        errors.append(
            f"is_high_priority: got {actual.is_high_priority}, "
            "expected {expected.is_high_priority}"
        )

    if actual.repeat_task != expected.repeat_task:
        errors.append(
            f"repeat_task: got '{actual.repeat_task}', "
            "expected '{expected.repeat_task}'"
        )

    def normalize_date(date_val):
        return "" if date_val is None or date_val == "" else str(date_val)

    date_fields = [
        ("do_date", actual.do_date, expected.do_date),
        ("due_date", actual.due_date, expected.due_date),
        ("completed_at", actual.completed_at, expected.completed_at),
    ]

    for field_name, actual_val, expected_val in date_fields:
        if normalize_date(actual_val) != normalize_date(expected_val):
            errors.append(
                f"{field_name}: got '{actual_val}', expected '{expected_val}'"
            )

    if errors:
        error_msg = f"TaskItem mismatch for '{actual.title}':\n"
        error_msg += "\n".join(f"  • {error}" for error in errors)
        raise AssertionError(error_msg)


def assert_archive_equal(actual: ArchiveItem, expected: ArchiveItem) -> None:
    errors = []

    if actual.title != expected.title:
        errors.append(f"Title: got '{actual.title}', expected '{expected.title}'")

    if actual.content != expected.content:
        errors.append(f"Content: got '{actual.content}', expected '{expected.content}'")

    if actual.tags != expected.tags:
        errors.append(f"Tags: got {actual.tags}, expected {expected.tags}")

    if actual.URL != expected.URL:
        errors.append(f"URL: got '{actual.URL}', expected '{expected.URL}'")

    if errors:
        error_msg = f"ArchiveItem mismatch for '{actual.title}':\n"
        error_msg += "\n".join(f"  • {error}" for error in errors)
        raise AssertionError(error_msg)


def assert_vault_file_exists(vault_path: Path, relative_path: str) -> None:
    file_path = vault_path / relative_path
    if not file_path.exists():
        existing_files = [
            str(f.relative_to(vault_path)) for f in vault_path.rglob("*") if f.is_file()
        ]
        raise AssertionError(
            f"Expected file '{relative_path}' not found in vault.\n"
            f"Existing files: {existing_files}"
        )


def assert_vault_file_not_exists(vault_path: Path, relative_path: str) -> None:
    file_path = vault_path / relative_path
    if file_path.exists():
        raise AssertionError(f"File '{relative_path}' should not exist but was found")


def assert_vault_file_contains(
    vault_path: Path, relative_path: str, expected_content: str
) -> None:
    file_path = vault_path / relative_path

    if not file_path.exists():
        raise AssertionError(
            f"Cannot check content: file '{relative_path}' does not exist"
        )

    actual_content = file_path.read_text()
    if expected_content not in actual_content:
        raise AssertionError(
            f"File '{relative_path}' does not contain expected content.\n"
            f"Expected to find: '{expected_content}'\n"
            f"Actual content: '{actual_content}'"
        )
