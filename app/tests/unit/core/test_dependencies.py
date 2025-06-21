from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.src.core.dependencies import (
    get_file_locker,
    get_git_manager,
    get_task_processor,
    get_task_service,
    get_vault_config,
    get_vault_manager,
)


class TestGetFileLocker:
    """Test get_file_locker dependency function."""

    def test_returns_file_locker_instance(self):
        """Test that get_file_locker returns a FileLocker instance."""
        from app.src.infrastructure.locking.file_locker import FileLocker

        locker = get_file_locker()
        assert isinstance(locker, FileLocker)

    def test_returns_same_instance_on_multiple_calls(self):
        """Test that get_file_locker returns the same instance (cached)."""
        locker1 = get_file_locker()
        locker2 = get_file_locker()
        assert locker1 is locker2

    def test_cached_behavior_with_lru_cache(self):
        """Test that the function is properly cached with lru_cache."""
        # Clear cache first
        get_file_locker.cache_clear()

        # First call
        locker1 = get_file_locker()

        # Second call should return same instance
        locker2 = get_file_locker()
        assert locker1 is locker2

        # Check cache info
        cache_info = get_file_locker.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1


class TestGetVaultConfig:
    """Test get_vault_config dependency function."""

    def test_returns_dict_when_get_config_returns_dict(self):
        """Test successful vault config retrieval."""
        mock_config = {"key1": "value1", "key2": "value2"}

        with patch("app.src.core.dependencies.get_config") as mock_get_config:
            mock_get_config.return_value = mock_config

            # Clear cache to ensure fresh call
            get_vault_config.cache_clear()

            result = get_vault_config()
            assert result == mock_config
            assert isinstance(result, dict)
            mock_get_config.assert_called_once()

    def test_raises_type_error_when_get_config_returns_non_dict(self):
        """Test that TypeError is raised when get_config returns non-dict."""
        test_cases = [
            "string",
            123,
            ["list"],
            None,
            object(),
        ]

        for invalid_config in test_cases:
            with patch("app.src.core.dependencies.get_config") as mock_get_config:
                mock_get_config.return_value = invalid_config

                get_vault_config.cache_clear()

                with pytest.raises(TypeError) as exc_info:
                    get_vault_config()

                assert (
                    f"Expected dict from get_config(), got {type(invalid_config)}"
                    in str(exc_info.value)
                )

    def test_cached_behavior(self):
        """Test that get_vault_config properly caches results."""
        mock_config = {"cached": "config"}

        with patch("app.src.core.dependencies.get_config") as mock_get_config:
            mock_get_config.return_value = mock_config

            get_vault_config.cache_clear()

            # First call
            result1 = get_vault_config()
            # Second call should use cache
            result2 = get_vault_config()

            assert result1 is result2
            assert mock_get_config.call_count == 1


class TestGetVaultManager:
    """Test get_vault_manager dependency function."""

    def test_returns_vault_manager_with_valid_settings(self):
        """Test successful VaultManager creation."""
        import tempfile

        from app.src.infrastructure.vault_manager import VaultManager

        # Create a real temporary directory for the vault path
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            mock_settings = MagicMock()
            mock_settings.vault_path = vault_path
            mock_file_locker = MagicMock()

            with (
                patch("app.src.core.dependencies.get_settings") as mock_get_settings,
                patch(
                    "app.src.core.dependencies.get_file_locker"
                ) as mock_get_file_locker,
            ):
                mock_get_settings.return_value = mock_settings
                mock_get_file_locker.return_value = mock_file_locker

                get_vault_manager.cache_clear()

                result = get_vault_manager()

                assert isinstance(result, VaultManager)
                mock_get_settings.assert_called_once()
                mock_get_file_locker.assert_called_once()

    def test_raises_value_error_when_vault_path_is_none(self):
        """Test that ValueError is raised when vault_path is None."""
        mock_settings = MagicMock()
        mock_settings.vault_path = None

        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            get_vault_manager.cache_clear()

            with pytest.raises(ValueError) as exc_info:
                get_vault_manager()

            assert "Vault path is not configured" in str(exc_info.value)
            assert "Set VAULT_PATH environment variable" in str(exc_info.value)

    def test_cached_behavior(self):
        """Test that get_vault_manager properly caches results."""
        import tempfile

        # Create a real temporary directory for the vault path
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            mock_settings = MagicMock()
            mock_settings.vault_path = vault_path
            mock_file_locker = MagicMock()

            with (
                patch("app.src.core.dependencies.get_settings") as mock_get_settings,
                patch(
                    "app.src.core.dependencies.get_file_locker"
                ) as mock_get_file_locker,
            ):
                mock_get_settings.return_value = mock_settings
                mock_get_file_locker.return_value = mock_file_locker

                get_vault_manager.cache_clear()

                # First call
                result1 = get_vault_manager()
                # Second call should use cache
                result2 = get_vault_manager()

                assert result1 is result2
                assert mock_get_settings.call_count == 1
                assert mock_get_file_locker.call_count == 1


class TestGetGitManager:
    """Test get_git_manager dependency function."""

    def test_returns_git_manager_when_git_directory_exists(self):
        """Test successful GitManager creation when .git exists."""
        from app.src.infrastructure.git.git_manager import GitManager

        mock_settings = MagicMock()
        mock_vault_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = True
        mock_vault_path.__truediv__.return_value = mock_git_dir
        mock_settings.vault_path = mock_vault_path

        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            get_git_manager.cache_clear()

            result = get_git_manager()

            assert isinstance(result, GitManager)
            mock_vault_path.__truediv__.assert_called_once_with(".git")
            mock_git_dir.exists.assert_called_once()

    def test_returns_none_when_vault_path_is_none(self):
        """Test that None is returned when vault_path is None."""
        mock_settings = MagicMock()
        mock_settings.vault_path = None

        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            get_git_manager.cache_clear()

            result = get_git_manager()

            assert result is None

    def test_returns_none_when_git_directory_does_not_exist(self):
        """Test that None is returned when .git directory doesn't exist."""
        mock_settings = MagicMock()
        mock_vault_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = False
        mock_vault_path.__truediv__.return_value = mock_git_dir
        mock_settings.vault_path = mock_vault_path

        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            get_git_manager.cache_clear()

            result = get_git_manager()

            assert result is None
            mock_git_dir.exists.assert_called_once()

    def test_returns_none_when_exception_occurs(self):
        """Test that None is returned when any exception occurs."""
        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.side_effect = Exception("Test exception")

            get_git_manager.cache_clear()

            result = get_git_manager()

            assert result is None

    def test_cached_behavior(self):
        """Test that get_git_manager properly caches results."""
        mock_settings = MagicMock()
        mock_vault_path = MagicMock()
        mock_git_dir = MagicMock()
        mock_git_dir.exists.return_value = True
        mock_vault_path.__truediv__.return_value = mock_git_dir
        mock_settings.vault_path = mock_vault_path

        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings

            get_git_manager.cache_clear()

            # First call
            result1 = get_git_manager()
            # Second call should use cache
            result2 = get_git_manager()

            assert result1 is result2
            assert mock_get_settings.call_count == 1


class TestGetTaskProcessor:
    """Test get_task_processor dependency function."""

    def test_returns_task_processor_instance(self):
        """Test that get_task_processor returns a TaskProcessor instance."""
        from app.src.domain.task_processor import TaskProcessor

        result = get_task_processor()

        assert isinstance(result, TaskProcessor)

    def test_returns_new_instance_each_call(self):
        """Test that get_task_processor returns new instances (not cached)."""
        result1 = get_task_processor()
        result2 = get_task_processor()

        # Should be different instances since it's not cached
        assert result1 is not result2


class TestGetTaskService:
    """Test get_task_service dependency function."""

    def test_returns_task_service_with_all_dependencies(self):
        """Test successful TaskService creation with all dependencies."""
        from app.src.services.task_service import TaskService

        mock_vault_manager = MagicMock()
        mock_task_processor = MagicMock()
        mock_config = {"test": "config"}
        mock_git_manager = MagicMock()

        with (
            patch(
                "app.src.core.dependencies.get_vault_manager"
            ) as mock_get_vault_manager,
            patch(
                "app.src.core.dependencies.get_task_processor"
            ) as mock_get_task_processor,
            patch(
                "app.src.core.dependencies.get_vault_config"
            ) as mock_get_vault_config,
            patch("app.src.core.dependencies.get_git_manager") as mock_get_git_manager,
        ):
            mock_get_vault_manager.return_value = mock_vault_manager
            mock_get_task_processor.return_value = mock_task_processor
            mock_get_vault_config.return_value = mock_config
            mock_get_git_manager.return_value = mock_git_manager

            result = get_task_service()

            assert isinstance(result, TaskService)
            mock_get_vault_manager.assert_called_once()
            mock_get_task_processor.assert_called_once()
            mock_get_vault_config.assert_called_once()
            mock_get_git_manager.assert_called_once()

    def test_returns_task_service_with_none_git_manager(self):
        """Test TaskService creation when git_manager is None."""
        from app.src.services.task_service import TaskService

        mock_vault_manager = MagicMock()
        mock_task_processor = MagicMock()
        mock_config = {"test": "config"}

        with (
            patch(
                "app.src.core.dependencies.get_vault_manager"
            ) as mock_get_vault_manager,
            patch(
                "app.src.core.dependencies.get_task_processor"
            ) as mock_get_task_processor,
            patch(
                "app.src.core.dependencies.get_vault_config"
            ) as mock_get_vault_config,
            patch("app.src.core.dependencies.get_git_manager") as mock_get_git_manager,
        ):
            mock_get_vault_manager.return_value = mock_vault_manager
            mock_get_task_processor.return_value = mock_task_processor
            mock_get_vault_config.return_value = mock_config
            mock_get_git_manager.return_value = None

            result = get_task_service()

            assert isinstance(result, TaskService)

    def test_returns_new_instance_each_call(self):
        """Test that get_task_service returns new instances (not cached)."""
        mock_vault_manager = MagicMock()
        mock_task_processor = MagicMock()
        mock_config = {"test": "config"}
        mock_git_manager = MagicMock()

        with (
            patch(
                "app.src.core.dependencies.get_vault_manager"
            ) as mock_get_vault_manager,
            patch(
                "app.src.core.dependencies.get_task_processor"
            ) as mock_get_task_processor,
            patch(
                "app.src.core.dependencies.get_vault_config"
            ) as mock_get_vault_config,
            patch("app.src.core.dependencies.get_git_manager") as mock_get_git_manager,
        ):
            mock_get_vault_manager.return_value = mock_vault_manager
            mock_get_task_processor.return_value = mock_task_processor
            mock_get_vault_config.return_value = mock_config
            mock_get_git_manager.return_value = mock_git_manager

            result1 = get_task_service()
            result2 = get_task_service()

            # Should be different instances since it's not cached
            assert result1 is not result2


class TestDependencyIntegration:
    """Test integration between dependency functions."""

    def test_all_cached_functions_use_lru_cache(self):
        """Test that cached functions have lru_cache attributes."""
        cached_functions = [
            get_file_locker,
            get_vault_config,
            get_vault_manager,
            get_git_manager,
        ]

        for func in cached_functions:
            assert hasattr(func, "cache_info")
            assert hasattr(func, "cache_clear")
            assert callable(func.cache_info)
            assert callable(func.cache_clear)

    def test_non_cached_functions_do_not_have_cache(self):
        """Test that non-cached functions don't have lru_cache attributes."""
        non_cached_functions = [
            get_task_processor,
            get_task_service,
        ]

        for func in non_cached_functions:
            assert not hasattr(func, "cache_info")
            assert not hasattr(func, "cache_clear")

    def test_vault_manager_depends_on_file_locker(self):
        """Test that get_vault_manager calls get_file_locker."""
        import tempfile

        # Create a real temporary directory for the vault path
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)

            mock_settings = MagicMock()
            mock_settings.vault_path = vault_path

            with (
                patch("app.src.core.dependencies.get_settings") as mock_get_settings,
                patch(
                    "app.src.core.dependencies.get_file_locker"
                ) as mock_get_file_locker,
            ):
                mock_get_settings.return_value = mock_settings
                mock_file_locker = MagicMock()
                mock_get_file_locker.return_value = mock_file_locker

                get_vault_manager.cache_clear()
                get_vault_manager()

                mock_get_file_locker.assert_called_once()

    def test_task_service_integrates_all_dependencies(self):
        """Test that get_task_service integrates all required dependencies."""
        mock_vault_manager = MagicMock()
        mock_task_processor = MagicMock()
        mock_config = {"integration": "test"}
        mock_git_manager = MagicMock()

        with (
            patch(
                "app.src.core.dependencies.get_vault_manager"
            ) as mock_get_vault_manager,
            patch(
                "app.src.core.dependencies.get_task_processor"
            ) as mock_get_task_processor,
            patch(
                "app.src.core.dependencies.get_vault_config"
            ) as mock_get_vault_config,
            patch("app.src.core.dependencies.get_git_manager") as mock_get_git_manager,
        ):
            mock_get_vault_manager.return_value = mock_vault_manager
            mock_get_task_processor.return_value = mock_task_processor
            mock_get_vault_config.return_value = mock_config
            mock_get_git_manager.return_value = mock_git_manager

            result = get_task_service()

            # Verify all dependencies were called
            mock_get_vault_manager.assert_called_once()
            mock_get_task_processor.assert_called_once()
            mock_get_vault_config.assert_called_once()
            mock_get_git_manager.assert_called_once()

            # Verify TaskService was created
            from app.src.services.task_service import TaskService

            assert isinstance(result, TaskService)


class TestErrorHandling:
    """Test error handling in dependency functions."""

    def test_get_vault_manager_propagates_get_settings_errors(self):
        """Test that get_vault_manager propagates errors from get_settings."""
        with patch("app.src.core.dependencies.get_settings") as mock_get_settings:
            mock_get_settings.side_effect = RuntimeError("Settings error")

            get_vault_manager.cache_clear()

            with pytest.raises(RuntimeError, match="Settings error"):
                get_vault_manager()

    def test_get_vault_config_propagates_get_config_errors(self):
        """Test that get_vault_config propagates errors from get_config."""
        with patch("app.src.core.dependencies.get_config") as mock_get_config:
            mock_get_config.side_effect = RuntimeError("Config error")

            get_vault_config.cache_clear()

            with pytest.raises(RuntimeError, match="Config error"):
                get_vault_config()

    def test_get_task_service_propagates_dependency_errors(self):
        """Test that get_task_service propagates errors from dependencies."""
        with patch(
            "app.src.core.dependencies.get_vault_manager"
        ) as mock_get_vault_manager:
            mock_get_vault_manager.side_effect = ValueError("Vault error")

            with pytest.raises(ValueError, match="Vault error"):
                get_task_service()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
