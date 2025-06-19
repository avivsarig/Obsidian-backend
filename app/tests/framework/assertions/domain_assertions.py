from app.src.domain.entities import ArchiveItem, TaskItem


class DomainAssertions:
    @staticmethod
    def assert_task_equal(actual: TaskItem, expected: TaskItem) -> None:
        errors = []

        if actual.title != expected.title:
            errors.append(f"title: {actual.title!r} != {expected.title!r}")

        if actual.content != expected.content:
            errors.append(f"content: {actual.content!r} != {expected.content!r}")

        if actual.done != expected.done:
            errors.append(f"done: {actual.done} != {expected.done}")

        if actual.is_project != expected.is_project:
            errors.append(f"is_project: {actual.is_project} != {expected.is_project}")

        # Date comparison with normalization
        for field in ["do_date", "due_date", "completed_at"]:
            actual_val = str(getattr(actual, field) or "")
            expected_val = str(getattr(expected, field) or "")
            if actual_val != expected_val:
                errors.append(f"{field}: {actual_val!r} != {expected_val!r}")

        if errors:
            raise AssertionError(
                "TaskItem mismatch:\n" + "\n".join(f"  • {e}" for e in errors)
            )

    @staticmethod
    def assert_archive_equal(actual: ArchiveItem, expected: ArchiveItem) -> None:
        errors = []

        if actual.title != expected.title:
            errors.append(f"title: {actual.title!r} != {expected.title!r}")

        if actual.content != expected.content:
            errors.append(f"content: {actual.content!r} != {expected.content!r}")

        if actual.tags != expected.tags:
            errors.append(f"tags: {actual.tags} != {expected.tags}")

        if errors:
            raise AssertionError(
                "ArchiveItem mismatch:\n" + "\n".join(f"  • {e}" for e in errors)
            )
