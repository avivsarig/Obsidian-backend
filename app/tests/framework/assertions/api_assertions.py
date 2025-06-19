from typing import Any

from fastapi import status


class APIAssertions:
    @staticmethod
    def assert_success(
        response: Any,
        expected_status: int = status.HTTP_200_OK,
    ) -> None:
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

    @staticmethod
    def assert_error(
        response: Any,
        expected_status: int,
        expected_error: str | None = None,
    ) -> None:
        assert (
            response.status_code == expected_status
        ), f"Expected error {expected_status}, got {response.status_code}"

        if expected_error:
            data = response.json()
            assert expected_error in data.get(
                "error", ""
            ), f"Expected error containing '{expected_error}', got: {data}"

    @staticmethod
    def assert_task_response(
        response: Any,
        expected_task: dict,
    ) -> None:
        APIAssertions.assert_success(response)
        data = response.json()

        for key, expected_value in expected_task.items():
            assert (
                data.get(key) == expected_value
            ), f"Task field '{key}': expected {expected_value}, got {data.get(key)}"

    @staticmethod
    def assert_task_list_response(
        response: Any, expected_count: int | None = None
    ) -> None:
        APIAssertions.assert_success(response)
        data = response.json()

        assert "tasks" in data, "Response should contain 'tasks' field"
        assert "total" in data, "Response should contain 'total' field"

        if expected_count is not None:
            assert (
                data["total"] == expected_count
            ), f"Expected {expected_count} tasks, got {data['total']}"
