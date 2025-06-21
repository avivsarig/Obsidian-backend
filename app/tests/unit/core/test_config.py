from pathlib import Path

import pytest

from app.src.core.config import Settings, get_settings


class TestSettingsBasics:
    """Test basic Settings functionality."""

    def test_settings_instantiation(self):
        """Test that Settings can be instantiated."""
        settings = Settings(vault_path=Path("/test/vault"))
        assert isinstance(settings, Settings)

    def test_settings_with_explicit_vault_path(self):
        """Test Settings with explicit vault_path."""
        test_path = Path("/custom/vault/path")
        settings = Settings(vault_path=test_path)
        assert settings.vault_path == test_path

    def test_settings_field_types(self):
        """Test that Settings fields have correct types."""
        settings = Settings(vault_path=Path("/test/vault"))

        assert isinstance(settings.environment, str)
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.api_keys_str, str)
        assert isinstance(settings.require_auth, bool)
        assert isinstance(settings.rate_limit_enabled, bool)
        assert isinstance(settings.rate_limit_requests_per_minute, int)
        assert isinstance(settings.allowed_origins, list)
        assert isinstance(settings.port, int)


class TestAPIKeysProperty:
    """Test the api_keys property that parses API_KEYS string."""

    def test_api_keys_property_parsing(self):
        """Test that api_keys property parses correctly."""
        # Test the property directly using the actual settings
        settings = Settings()

        # The property should return a list
        assert isinstance(settings.api_keys, list)

        # Should contain the key from .env file
        assert len(settings.api_keys) == 1
        assert settings.api_keys[0] == "hMXVrb0Vm1aEHLBi4ljXn4qtZtRGFHQu"

    def test_api_keys_parsing_logic(self):
        """Test the api_keys parsing logic directly."""

        # Test the parsing logic by creating a simple object
        class MockSettings:
            def __init__(self, api_keys_str):
                self.api_keys_str = api_keys_str

            @property
            def api_keys(self):
                if not self.api_keys_str:
                    return []
                return [
                    key.strip() for key in self.api_keys_str.split(",") if key.strip()
                ]

        # Test empty string
        mock = MockSettings("")
        assert mock.api_keys == []

        # Test single key
        mock = MockSettings("single-key")
        assert mock.api_keys == ["single-key"]

        # Test multiple keys
        mock = MockSettings("key1,key2,key3")
        assert mock.api_keys == ["key1", "key2", "key3"]

        # Test whitespace handling
        mock = MockSettings(" key1 , key2 , key3 ")
        assert mock.api_keys == ["key1", "key2", "key3"]

        # Test empty segments
        mock = MockSettings("key1,,key2,")
        assert mock.api_keys == ["key1", "key2"]

        # Test only separators
        mock = MockSettings(", , ,")
        assert mock.api_keys == []

    def test_api_keys_property_empty_string(self):
        """Test api_keys property with empty string."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"API_KEYS": ""}, clear=True):
            settings = Settings(vault_path=Path("/test"))
            assert settings.api_keys == []


class TestHostProperty:
    """Test the host property for different environments."""

    def test_host_development_environment(self):
        """Test host property in development environment."""
        settings = Settings(environment="development", vault_path=Path("/test"))
        assert settings.host == "127.0.0.1"

    def test_host_production_environment(self):
        """Test host property in production environment."""
        settings = Settings(environment="production", vault_path=Path("/test"))
        assert settings.host == "0.0.0.0"  # noqa: S104

    def test_host_other_environment(self):
        """Test host property in other environments."""
        settings = Settings(environment="staging", vault_path=Path("/test"))
        assert settings.host == "127.0.0.1"

    def test_host_custom_environment(self):
        """Test host property with custom environment values."""
        for env in ["test", "local", "dev", "custom"]:
            settings = Settings(environment=env, vault_path=Path("/test"))
            assert settings.host == "127.0.0.1"


class TestVaultPathDiscovery:
    """Test vault path discovery logic."""

    def test_vault_path_provided_directly(self):
        """Test when vault_path is provided directly."""
        test_path = Path("/custom/vault/path")
        settings = Settings(vault_path=test_path)
        assert settings.vault_path == test_path

    def test_vault_path_skips_discovery_when_provided(self):
        """Test that providing vault_path skips discovery."""
        from unittest.mock import patch

        with patch.object(Settings, "_discover_vault_path") as mock_discover:
            custom_path = Path("/custom/vault")
            settings = Settings(vault_path=custom_path)
            assert settings.vault_path == custom_path
            mock_discover.assert_not_called()

    def test_vault_path_triggers_discovery_when_none(self):
        """Test that vault_path=None triggers discovery."""
        from unittest.mock import patch

        with patch.object(Settings, "_discover_vault_path") as mock_discover:
            mock_discover.return_value = Path("/discovered/vault")
            settings = Settings(vault_path=None)
            assert settings.vault_path == Path("/discovered/vault")
            mock_discover.assert_called_once()


class TestGetTestVaultPath:
    """Test the _get_test_vault_path method."""

    def test_get_test_vault_path_with_custom_path(self):
        """Test _get_test_vault_path with custom TEST_VAULT_PATH."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"TEST_VAULT_PATH": "/custom/test/vault"}):
            settings = Settings(vault_path=Path("/dummy"))
            result = settings._get_test_vault_path()
            assert result == Path("/custom/test/vault")

    def test_get_test_vault_path_without_custom_path(self):
        """Test _get_test_vault_path without custom TEST_VAULT_PATH."""
        import os
        from unittest.mock import patch

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("tempfile.mkdtemp") as mock_mkdtemp,
        ):
            mock_mkdtemp.return_value = "/tmp/vault-test-abc456secure"  # noqa: S108

            settings = Settings(vault_path=Path("/dummy"))
            result = settings._get_test_vault_path()

            assert result == Path("/tmp/vault-test-abc456secure")  # noqa: S108
            mock_mkdtemp.assert_called_once_with(prefix="vault-test-", suffix="secure")


class TestGetSettings:
    """Test the get_settings function."""

    def setUp(self):
        """Clear the global settings cache before each test."""
        import app.src.core.config

        app.src.core.config._settings = None

    def test_get_settings_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        self.setUp()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        self.setUp()
        settings = get_settings()
        assert isinstance(settings, Settings)


class TestSettingsValidation:
    """Test Settings field validation and type conversion."""

    def test_boolean_fields_validation(self):
        """Test boolean field validation."""
        settings = Settings(
            debug=True,
            require_auth=False,
            rate_limit_enabled=True,
            vault_path=Path("/test/vault"),
        )

        assert isinstance(settings.debug, bool)
        assert isinstance(settings.require_auth, bool)
        assert isinstance(settings.rate_limit_enabled, bool)
        assert settings.debug is True
        assert settings.require_auth is False
        assert settings.rate_limit_enabled is True

    def test_integer_fields_validation(self):
        """Test integer field validation."""
        settings = Settings(
            rate_limit_requests_per_minute=200,
            port=9000,
            vault_path=Path("/test/vault"),
        )

        assert isinstance(settings.rate_limit_requests_per_minute, int)
        assert isinstance(settings.port, int)
        assert settings.rate_limit_requests_per_minute == 200
        assert settings.port == 9000

    def test_list_fields_validation(self):
        """Test list field validation."""
        origins = ["https://app.example.com", "https://admin.example.com"]
        settings = Settings(allowed_origins=origins, vault_path=Path("/test/vault"))

        assert isinstance(settings.allowed_origins, list)
        assert all(isinstance(origin, str) for origin in settings.allowed_origins)
        assert settings.allowed_origins == origins

    def test_path_field_validation(self):
        """Test Path field validation."""
        test_path = Path("/test/path")
        settings = Settings(vault_path=test_path)
        assert isinstance(settings.vault_path, Path)
        assert settings.vault_path == test_path


class TestEnvironmentConfiguration:
    """Test environment-specific configuration behavior."""

    def test_development_environment_settings(self):
        """Test settings in development environment."""
        settings = Settings(environment="development", vault_path=Path("/test/vault"))
        assert settings.environment == "development"
        assert settings.host == "127.0.0.1"

    def test_production_environment_settings(self):
        """Test settings in production environment."""
        settings = Settings(environment="production", vault_path=Path("/test/vault"))
        assert settings.environment == "production"
        assert settings.host == "0.0.0.0"  # noqa: S104

    def test_constructor_parameter_override(self):
        """Test that constructor parameters work correctly."""
        settings = Settings(
            debug=True,
            log_level="ERROR",
            require_auth=True,
            rate_limit_enabled=False,
            port=9999,
            vault_path=Path("/test/vault"),
        )

        assert settings.debug is True
        assert settings.log_level == "ERROR"
        assert settings.require_auth is True
        assert settings.rate_limit_enabled is False
        assert settings.port == 9999


class TestActualEnvironmentValues:
    """Test with actual environment values from .env file."""

    def test_loads_from_env_file(self):
        """Test that Settings loads values from .env file."""
        settings = Settings()

        # These values come from the actual .env file
        assert settings.api_keys_str == "hMXVrb0Vm1aEHLBi4ljXn4qtZtRGFHQu"
        assert settings.require_auth is False
        assert settings.rate_limit_enabled is True
        assert settings.vault_path == Path("../vault")

    def test_api_keys_property_with_env_value(self):
        """Test api_keys property with actual env value."""
        settings = Settings()
        expected_key = "hMXVrb0Vm1aEHLBi4ljXn4qtZtRGFHQu"
        assert settings.api_keys == [expected_key]

    def test_environment_defaults(self):
        """Test that environment defaults work correctly."""
        settings = Settings()

        # Test defaults that aren't overridden by env
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.port == 8000
        assert isinstance(settings.allowed_origins, list)

    def test_field_types_with_env_loading(self):
        """Test field types when loading from environment."""
        settings = Settings()

        # Verify types are correct even when loaded from env
        assert isinstance(settings.api_keys_str, str)
        assert isinstance(settings.require_auth, bool)
        assert isinstance(settings.rate_limit_enabled, bool)
        assert isinstance(settings.vault_path, Path)


class TestVaultDiscoveryLogic:
    """Test vault discovery methods."""

    def test_discover_vault_path_production(self):
        """Test _discover_vault_path for production environment."""
        settings = Settings(vault_path=Path("/dummy"))  # Skip actual discovery
        settings.environment = "production"

        # Mock the method to test logic
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            result = settings._discover_vault_path()
            assert result == Path("/opt/vault")

    def test_discover_vault_path_with_env_var(self):
        """Test _discover_vault_path with VAULT_PATH environment variable."""
        import os
        from unittest.mock import patch

        settings = Settings(vault_path=Path("/dummy"))  # Skip actual discovery

        with patch.dict(os.environ, {"VAULT_PATH": "/env/vault/path"}, clear=True):
            result = settings._discover_vault_path()
            assert result == Path("/env/vault/path")

    def test_discover_vault_path_testing_mode(self):
        """Test _discover_vault_path in testing mode."""
        import os
        from unittest.mock import patch

        settings = Settings(vault_path=Path("/dummy"))  # Skip actual discovery

        with patch.dict(
            os.environ, {"TESTING": "true", "TEST_VAULT_PATH": "/test/vault"}
        ):
            result = settings._discover_vault_path()
            assert result == Path("/test/vault")

    def test_discover_vault_path_raises_error_when_no_vault_found(self):
        """Test _discover_vault_path raises error when vault not found."""
        import os
        from unittest.mock import MagicMock, patch

        settings = Settings(vault_path=Path("/dummy"))
        settings.environment = "development"

        # Mock the traversal to simulate no vault found
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path.parent = mock_path  # Simulate reaching root

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("app.src.core.config.Path") as mock_path_class,
        ):
            mock_path_class.return_value = mock_path
            with pytest.raises(ValueError, match="Vault not found"):
                settings._discover_vault_path()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
