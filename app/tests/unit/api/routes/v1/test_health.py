import builtins
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tests.framework import (
    APIAssertions,
    VaultAssertions,
)


class TestHealthEndpoint:
    def test_health_check_success(self, api_client, vault_env):
        VaultAssertions.assert_vault_structure(vault_env.vault_path)

        (vault_env.vault_path / "test_file.md").write_text("test content")
        (vault_env.vault_path / "Tasks" / "task.md").write_text("task content")

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

        APIAssertions.assert_success(response)

        data = response.json()
        assert data["status"] == "ok"
        assert data["vault_status"] == "ok"
        assert data["vault_file_count"] >= 2
        assert data["git_status"] in ["ok", "unavailable"]
        assert "timestamp" in data

        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_check_cache_headers(self, api_client, vault_env):
        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

        assert (
            response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
        )
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

    def test_health_check_vault_missing(self, api_client):
        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = None

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["status"] == "error"
            assert data["vault_status"] == "error"
            assert data["vault_file_count"] == 0

    def test_health_check_vault_nonexistent_path(self, api_client):
        nonexistent_path = Path("/nonexistent/vault/path")

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = nonexistent_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["status"] == "error"
            assert data["vault_status"] == "error"
            assert data["vault_file_count"] == 0

    def test_health_check_vault_permission_error(self, api_client, vault_env):
        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch(
                "app.src.api.routes.v1.health._count_files_recursive",
                side_effect=OSError("Permission denied"),
            ),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["status"] == "error"
            assert data["vault_status"] == "error"
            assert data["vault_file_count"] == 0

    def test_health_check_git_available(self, api_client, vault_env):
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("git.Repo", return_value=mock_repo),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["git_status"] == "ok"

    def test_health_check_git_invalid_head(self, api_client, vault_env):
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = False

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("git.Repo", return_value=mock_repo),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["git_status"] == "error"
            assert data["status"] == "error"

    def test_health_check_git_import_error(self, api_client, vault_env):
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "git":
                raise ImportError("git not available")
            return original_import(name, *args, **kwargs)

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("builtins.__import__", side_effect=mock_import),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["git_status"] == "unavailable"
            assert data["status"] == "ok"

    def test_health_check_git_repo_error(self, api_client, vault_env):
        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("git.Repo", side_effect=Exception("Invalid repository")),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["git_status"] == "unavailable"

    def test_file_count_recursive(self, api_client, vault_env):
        (vault_env.vault_path / "root_file.md").write_text("content")
        (vault_env.vault_path / "Tasks" / "task1.md").write_text("content")
        (vault_env.vault_path / "Tasks" / "task2.md").write_text("content")
        (vault_env.vault_path / "Tasks" / "Completed" / "done.md").write_text("content")

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

        APIAssertions.assert_success(response)
        data = response.json()

        assert data["vault_file_count"] == 4

    def test_file_count_with_nested_errors(self, api_client, vault_env):
        (vault_env.vault_path / "accessible.md").write_text("content")

        def mock_count_files(path):
            if "error" in str(path):
                raise OSError("Permission denied")
            return 1

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch(
                "app.src.api.routes.v1.health._count_files_recursive",
                side_effect=mock_count_files,
            ),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

            APIAssertions.assert_success(response)
            data = response.json()

            assert data["vault_file_count"] >= 0

    def test_file_count_symlink_handling(self, api_client, vault_env):
        regular_file = vault_env.vault_path / "regular.md"
        regular_file.write_text("content")

        regular_dir = vault_env.vault_path / "regular_dir"
        regular_dir.mkdir()
        (regular_dir / "nested.md").write_text("content")

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

        APIAssertions.assert_success(response)
        data = response.json()

        assert data["vault_file_count"] == 2

    def test_response_model_validation(self, api_client, vault_env):
        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            response = api_client.get("/api/v1/health")

        APIAssertions.assert_success(response)
        data = response.json()

        required_fields = [
            "status",
            "timestamp",
            "vault_status",
            "vault_file_count",
            "git_status",
        ]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"

        assert isinstance(data["vault_file_count"], int)
        assert data["vault_file_count"] >= 0
        assert data["status"] in ["ok", "error"]
        assert data["vault_status"] in ["ok", "error"]
        assert data["git_status"] in ["ok", "error", "unavailable"]


class TestHealthInternalFunctions:
    def test_check_vault_status_with_valid_vault(self, vault_env):
        from app.src.api.routes.v1.health import _check_vault_status_and_file_count

        (vault_env.vault_path / "test.md").write_text("content")

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = vault_env.vault_path

            status, count = _check_vault_status_and_file_count()

            assert status == "ok"
            assert count >= 1

    def test_check_vault_status_with_missing_vault(self):
        from app.src.api.routes.v1.health import _check_vault_status_and_file_count

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = None

            status, count = _check_vault_status_and_file_count()

            assert status == "error"
            assert count == 0

    def test_count_files_recursive_with_nested_structure(self, vault_env):
        from app.src.api.routes.v1.health import _count_files_recursive

        (vault_env.vault_path / "root.md").write_text("content")
        subdir = vault_env.vault_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("content")
        (subdir / "another.md").write_text("content")

        count = _count_files_recursive(vault_env.vault_path)

        assert count == 3

    def test_count_files_recursive_with_item_access_error(self, vault_env):
        from app.src.api.routes.v1.health import _count_files_recursive

        (vault_env.vault_path / "accessible.md").write_text("content")
        (vault_env.vault_path / "problematic.md").write_text("content")

        def mock_is_file(self):
            if "problematic" in str(self):
                raise OSError("File access denied")
            return str(self).endswith(".md")

        with patch("pathlib.Path.is_file", mock_is_file):
            count = _count_files_recursive(vault_env.vault_path)
            assert count == 1

    def test_count_files_recursive_with_permission_error(self, vault_env):
        from app.src.api.routes.v1.health import _count_files_recursive

        (vault_env.vault_path / "accessible.md").write_text("content")

        with patch("pathlib.Path.iterdir", side_effect=OSError("Permission denied")):
            count = _count_files_recursive(vault_env.vault_path)
            assert count == 0

    def test_check_git_status_unavailable_vault(self):
        from app.src.api.routes.v1.health import _check_git_status

        with patch("app.src.api.routes.v1.health.get_settings") as mock_settings:
            mock_settings.return_value.vault_path = None

            status = _check_git_status()

            assert status == "unavailable"

    def test_check_git_status_with_valid_repo(self, vault_env):
        from app.src.api.routes.v1.health import _check_git_status

        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("git.Repo", return_value=mock_repo),
        ):
            mock_settings.return_value.vault_path = vault_env.vault_path

            status = _check_git_status()

            assert status == "ok"

    def test_check_git_status_import_error(self):
        from app.src.api.routes.v1.health import _check_git_status

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "git":
                raise ImportError("git not available")
            return original_import(name, *args, **kwargs)

        with (
            patch("app.src.api.routes.v1.health.get_settings") as mock_settings,
            patch("builtins.__import__", side_effect=mock_import),
        ):
            mock_settings.return_value.vault_path = Path("/some/path")

            status = _check_git_status()

            assert status == "unavailable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
