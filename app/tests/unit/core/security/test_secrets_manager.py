import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.src.core.security.secrets_manager import SecretsManager


class TestSecretsManagerInit:
    """Test SecretsManager initialization."""

    @patch("app.src.core.security.secrets_manager.boto3")
    @patch("app.src.core.security.secrets_manager.get_settings")
    def test_default_initialization(self, mock_get_settings, mock_boto3):
        """Test default initialization with eu-west-1 region."""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        secrets_manager = SecretsManager()

        assert secrets_manager.settings is mock_settings
        mock_boto3.client.assert_called_once_with(
            "secretsmanager", region_name="eu-west-1"
        )

    @patch("app.src.core.security.secrets_manager.boto3")
    @patch("app.src.core.security.secrets_manager.get_settings")
    def test_custom_region_initialization(self, mock_get_settings, mock_boto3):
        """Test initialization with custom region."""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        SecretsManager(region_name="us-east-1")

        mock_boto3.client.assert_called_once_with(
            "secretsmanager", region_name="us-east-1"
        )


class TestGetApiKeys:
    """Test the get_api_keys method."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("app.src.core.security.secrets_manager.boto3"),
            patch(
                "app.src.core.security.secrets_manager.get_settings"
            ) as mock_get_settings,
        ):
            self.mock_settings = MagicMock()
            mock_get_settings.return_value = self.mock_settings
            self.secrets_manager = SecretsManager()

    @pytest.mark.asyncio
    async def test_no_key_name_configured(self):
        """Test behavior when no AWS key name is configured."""
        self.mock_settings.aws_secrets_manager_key_name = ""

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.warning.assert_called_once_with(
                "No AWS secrets manager key name configured"
            )

    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """Test successful API key retrieval."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {
            "SecretString": json.dumps({"api_keys": ["key1", "key2", "key3"]})
        }
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == ["key1", "key2", "key3"]
            mock_logger.debug.assert_called_once_with("Retrieved 3 API keys from AWS")

    @pytest.mark.asyncio
    async def test_empty_api_keys_list(self):
        """Test when secret contains empty api_keys list."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {"SecretString": json.dumps({"api_keys": []})}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        result = await self.secrets_manager.get_api_keys()
        assert result == []

    @pytest.mark.asyncio
    async def test_no_api_keys_field(self):
        """Test when secret doesn't contain api_keys field."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {"SecretString": json.dumps({"other_field": "value"})}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        result = await self.secrets_manager.get_api_keys()
        assert result == []

    @pytest.mark.asyncio
    async def test_api_keys_not_list(self):
        """Test when api_keys field is not a list."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {"SecretString": json.dumps({"api_keys": "not-a-list"})}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.error.assert_called_once_with(
                "API keys in secret is not a list"
            )

    @pytest.mark.asyncio
    async def test_mixed_data_types_in_list(self):
        """Test filtering of non-string values from api_keys list."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {
            "SecretString": json.dumps(
                {"api_keys": ["key1", 123, "key2", None, "", "key3", True]}
            )
        }
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            # Should only return valid string keys, filtering out empty strings
            assert result == ["key1", "key2", "key3"]
            mock_logger.debug.assert_called_once_with("Retrieved 3 API keys from AWS")

    @pytest.mark.asyncio
    async def test_client_error_handling(self):
        """Test handling of AWS ClientError."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        client_error = ClientError(
            error_response={"Error": {"Code": "ResourceNotFoundException"}},
            operation_name="GetSecretValue",
        )
        self.secrets_manager.client.get_secret_value = MagicMock(
            side_effect=client_error
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.error.assert_called_once()
            assert "Failed to retrieve API keys from AWS" in str(
                mock_logger.error.call_args
            )

    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self):
        """Test handling of invalid JSON in secret."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {"SecretString": "invalid-json{"}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.error.assert_called_once()
            assert "Invalid JSON in secret" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_secret_string_conversion(self):
        """Test that non-string values in list are converted to strings."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {
            "SecretString": json.dumps({"api_keys": ["string_key", "another_key"]})
        }
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        result = await self.secrets_manager.get_api_keys()

        # Ensure all returned values are strings
        assert all(isinstance(key, str) for key in result)
        assert result == ["string_key", "another_key"]

    @pytest.mark.asyncio
    async def test_large_api_keys_list(self):
        """Test handling of large number of API keys."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        large_key_list = [f"key_{i}" for i in range(100)]
        mock_response = {"SecretString": json.dumps({"api_keys": large_key_list})}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert len(result) == 100
            assert result == large_key_list
            mock_logger.debug.assert_called_once_with("Retrieved 100 API keys from AWS")


class TestSecretsManagerIntegration:
    """Integration tests for SecretsManager."""

    @patch("app.src.core.security.secrets_manager.boto3")
    @patch("app.src.core.security.secrets_manager.get_settings")
    def test_settings_integration(self, mock_get_settings, mock_boto3):
        """Test that SecretsManager properly integrates with settings."""
        mock_settings = MagicMock()
        mock_settings.aws_secrets_manager_key_name = "integration-test-secret"
        mock_get_settings.return_value = mock_settings

        secrets_manager = SecretsManager()

        assert (
            secrets_manager.settings.aws_secrets_manager_key_name
            == "integration-test-secret"
        )

    def test_logger_configuration(self):
        """Test that logger is properly configured."""
        # Import to trigger logger creation
        from app.src.core.security.secrets_manager import logger

        assert logger.name == "app.src.core.security.secrets_manager"
        assert isinstance(logger, logging.Logger)


class TestSecretsManagerErrorScenarios:
    """Test various error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("app.src.core.security.secrets_manager.boto3"),
            patch(
                "app.src.core.security.secrets_manager.get_settings"
            ) as mock_get_settings,
        ):
            self.mock_settings = MagicMock()
            mock_get_settings.return_value = self.mock_settings
            self.secrets_manager = SecretsManager()

    @pytest.mark.asyncio
    async def test_access_denied_error(self):
        """Test handling of access denied errors."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        access_denied_error = ClientError(
            error_response={"Error": {"Code": "AccessDeniedException"}},
            operation_name="GetSecretValue",
        )
        self.secrets_manager.client.get_secret_value = MagicMock(
            side_effect=access_denied_error
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_secret_string(self):
        """Test handling of empty secret string."""
        self.mock_settings.aws_secrets_manager_key_name = "test-secret"

        mock_response = {"SecretString": ""}
        self.secrets_manager.client.get_secret_value = MagicMock(
            return_value=mock_response
        )

        with patch("app.src.core.security.secrets_manager.logger") as mock_logger:
            result = await self.secrets_manager.get_api_keys()

            assert result == []
            mock_logger.error.assert_called_once()
            assert "Invalid JSON in secret" in str(mock_logger.error.call_args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
