from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.src.api.routes.v1.vault import GitPullResponse, pull_latest_changes
from app.src.core.dependencies import get_git_manager
from app.src.infrastructure.git.git_manager import GitManager
from app.tests.framework import APIAssertions


class TestVaultPullEndpoint:
    def test_pull_latest_changes_success(self, api_client):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = True
        mock_git_manager.current_branch = "main"
        mock_git_manager.pull_latest.return_value = True

        api_client._app.dependency_overrides[get_git_manager] = lambda: mock_git_manager
        try:
            response = api_client.post("/api/v1/vault/pull")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["success"] is True
            assert data["message"] == "Successfully pulled latest changes"
            assert data["current_branch"] == "main"
            assert data["repository_valid"] is True
        finally:
            api_client._app.dependency_overrides.clear()

    def test_pull_latest_changes_git_manager_none(self, api_client):
        api_client._app.dependency_overrides[get_git_manager] = lambda: None
        try:
            response = api_client.post("/api/v1/vault/pull")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Git repository not configured or not available"
        finally:
            api_client._app.dependency_overrides.clear()

    def test_pull_latest_changes_invalid_repository(self, api_client):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = False
        mock_git_manager.current_branch = "main"

        api_client._app.dependency_overrides[get_git_manager] = lambda: mock_git_manager
        try:
            response = api_client.post("/api/v1/vault/pull")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["success"] is False
            assert data["message"] == "Repository state validation failed"
            assert data["current_branch"] == "main"
            assert data["repository_valid"] is False
        finally:
            api_client._app.dependency_overrides.clear()

    def test_pull_latest_changes_pull_fails(self, api_client):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = True
        mock_git_manager.current_branch = "development"
        mock_git_manager.pull_latest.return_value = False

        api_client._app.dependency_overrides[get_git_manager] = lambda: mock_git_manager
        try:
            response = api_client.post("/api/v1/vault/pull")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["success"] is False
            assert (
                data["message"] == "Failed to pull changes - "
                "check repository state and remote connectivity"
            )
            assert data["current_branch"] == "development"
            assert data["repository_valid"] is True
        finally:
            api_client._app.dependency_overrides.clear()

    def test_pull_latest_changes_none_current_branch(self, api_client):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = True
        mock_git_manager.current_branch = None
        mock_git_manager.pull_latest.return_value = True

        api_client._app.dependency_overrides[get_git_manager] = lambda: mock_git_manager
        try:
            response = api_client.post("/api/v1/vault/pull")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["success"] is True
            assert data["message"] == "Successfully pulled latest changes"
            assert data["current_branch"] is None
            assert data["repository_valid"] is True
        finally:
            api_client._app.dependency_overrides.clear()


class TestVaultPullFunction:
    @pytest.mark.asyncio
    async def test_pull_latest_changes_function_success(self):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = True
        mock_git_manager.current_branch = "main"
        mock_git_manager.pull_latest.return_value = True

        result = await pull_latest_changes(mock_git_manager)

        assert isinstance(result, GitPullResponse)
        assert result.success is True
        assert result.message == "Successfully pulled latest changes"
        assert result.current_branch == "main"
        assert result.repository_valid is True

        mock_git_manager.validate_repository_state.assert_called_once()
        mock_git_manager.pull_latest.assert_called_once()

    @pytest.mark.asyncio
    async def test_pull_latest_changes_function_no_git_manager(self):
        with pytest.raises(HTTPException) as exc_info:
            await pull_latest_changes(None)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Git repository not configured or not available"

    @pytest.mark.asyncio
    async def test_pull_latest_changes_function_invalid_repository(self):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = False
        mock_git_manager.current_branch = "feature-branch"

        result = await pull_latest_changes(mock_git_manager)

        assert isinstance(result, GitPullResponse)
        assert result.success is False
        assert result.message == "Repository state validation failed"
        assert result.current_branch == "feature-branch"
        assert result.repository_valid is False

        mock_git_manager.validate_repository_state.assert_called_once()
        mock_git_manager.pull_latest.assert_not_called()

    @pytest.mark.asyncio
    async def test_pull_latest_changes_function_pull_failure(self):
        mock_git_manager = MagicMock(spec=GitManager)
        mock_git_manager.validate_repository_state.return_value = True
        mock_git_manager.current_branch = "main"
        mock_git_manager.pull_latest.return_value = False

        result = await pull_latest_changes(mock_git_manager)

        assert isinstance(result, GitPullResponse)
        assert result.success is False
        assert (
            result.message
            == "Failed to pull changes - check repository state and remote connectivity"
        )
        assert result.current_branch == "main"
        assert result.repository_valid is True

        mock_git_manager.validate_repository_state.assert_called_once()
        mock_git_manager.pull_latest.assert_called_once()


class TestGitPullResponseModel:
    def test_git_pull_response_model_creation(self):
        response = GitPullResponse(
            success=True,
            message="Test message",
            current_branch="main",
            repository_valid=True,
        )

        assert response.success is True
        assert response.message == "Test message"
        assert response.current_branch == "main"
        assert response.repository_valid is True

    def test_git_pull_response_model_optional_branch(self):
        response = GitPullResponse(
            success=False, message="Error message", repository_valid=False
        )

        assert response.success is False
        assert response.message == "Error message"
        assert response.current_branch is None
        assert response.repository_valid is False

    def test_git_pull_response_model_serialization(self):
        response = GitPullResponse(
            success=True,
            message="Success",
            current_branch="develop",
            repository_valid=True,
        )

        data = response.model_dump()
        expected = {
            "success": True,
            "message": "Success",
            "current_branch": "develop",
            "repository_valid": True,
        }

        assert data == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
