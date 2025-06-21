import pytest

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.system_exceptions import (
    BaseSystemException,
    OperationTimeoutError,
    SystemConfigurationError,
    SystemIntegrationError,
    SystemResourceError,
)


class TestBaseSystemException:
    """Test BaseSystemException class."""

    def test_inherits_from_base_api_exception(self):
        """Test that BaseSystemException inherits from BaseAPIException."""
        assert issubclass(BaseSystemException, BaseAPIException)

    def test_can_be_instantiated(self):
        """Test that BaseSystemException can be instantiated."""
        exception = BaseSystemException("Test system exception")

        assert isinstance(exception, BaseSystemException)
        assert isinstance(exception, BaseAPIException)
        assert exception.message == "Test system exception"

    def test_can_be_raised_and_caught(self):
        """Test that BaseSystemException can be raised and caught."""
        with pytest.raises(BaseSystemException) as exc_info:
            raise BaseSystemException("Test raising")

        assert exc_info.value.message == "Test raising"

    def test_can_be_caught_as_base_api_exception(self):
        """Test that BaseSystemException can be caught as BaseAPIException."""
        with pytest.raises(BaseAPIException) as exc_info:
            raise BaseSystemException("Test base catching")

        assert isinstance(exc_info.value, BaseSystemException)


class TestSystemConfigurationError:
    """Test SystemConfigurationError class."""

    def test_inherits_from_base_system_exception(self):
        """Test that SystemConfigurationError inherits from BaseSystemException."""
        assert issubclass(SystemConfigurationError, BaseSystemException)
        assert issubclass(SystemConfigurationError, BaseAPIException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = SystemConfigurationError("Custom config error")

        assert exception.message == "Custom config error"
        assert exception.status_code == 500
        assert (
            exception.detail
            == "Check application configuration and environment variables"
        )
        assert exception.setting is None

    def test_constructor_with_setting_generates_message(self):
        """Test that providing setting generates appropriate message."""
        exception = SystemConfigurationError(setting="DATABASE_URL")

        assert exception.message == "Configuration error: DATABASE_URL"
        assert exception.status_code == 500
        assert exception.setting == "DATABASE_URL"

    def test_constructor_without_message_or_setting(self):
        """Test creating exception without message or setting uses default."""
        exception = SystemConfigurationError()

        assert exception.message == "System configuration is invalid"
        assert exception.status_code == 500
        assert exception.setting is None

    def test_constructor_with_custom_detail(self):
        """Test creating exception with custom detail."""
        custom_detail = "Check the .env file for missing values"
        exception = SystemConfigurationError("Config error", detail=custom_detail)

        assert exception.detail == custom_detail

    def test_constructor_with_setting_and_custom_detail(self):
        """Test creating exception with setting and custom detail."""
        exception = SystemConfigurationError(
            setting="API_KEY", detail="API key is missing or invalid"
        )

        assert exception.message == "Configuration error: API_KEY"
        assert exception.detail == "API key is missing or invalid"
        assert exception.setting == "API_KEY"

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = SystemConfigurationError(
            message="Explicit config error", setting="REDIS_URL"
        )

        assert exception.message == "Explicit config error"
        assert exception.setting == "REDIS_URL"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = SystemConfigurationError(
            message="Custom configuration error",
            setting="JWT_SECRET",
            detail="Custom detail message",
        )

        assert exception.message == "Custom configuration error"
        assert exception.setting == "JWT_SECRET"
        assert exception.detail == "Custom detail message"
        assert exception.status_code == 500

    def test_default_detail_when_none_provided(self):
        """Test that default detail is set when none provided."""
        exception = SystemConfigurationError("Config error")

        assert (
            exception.detail
            == "Check application configuration and environment variables"
        )


class TestSystemIntegrationError:
    """Test SystemIntegrationError class."""

    def test_inherits_from_base_system_exception(self):
        """Test that SystemIntegrationError inherits from BaseSystemException."""
        assert issubclass(SystemIntegrationError, BaseSystemException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = SystemIntegrationError("Custom integration error")

        assert exception.message == "Custom integration error"
        assert exception.status_code == 502
        assert (
            exception.detail == "Check external service connectivity and authentication"
        )
        assert exception.system is None
        assert exception.operation is None

    def test_constructor_with_system_and_operation_generates_message(self):
        """Test that providing system and operation generates appropriate message."""
        exception = SystemIntegrationError(system="database", operation="query")

        assert exception.message == "Unable to connect to database for query"
        assert exception.system == "database"
        assert exception.operation == "query"

    def test_constructor_without_message_system_or_operation(self):
        """
        Test creating exception without message, system, or operation uses default.
        """
        exception = SystemIntegrationError()

        assert exception.message == "External service integration failed"
        assert exception.status_code == 502
        assert exception.system is None
        assert exception.operation is None

    def test_constructor_with_system_generates_detail(self):
        """Test that providing system generates appropriate detail."""
        exception = SystemIntegrationError("Integration failed", system="redis")

        assert exception.detail == "Check redis service status and credentials"
        assert exception.system == "redis"

    def test_constructor_with_original_error(self):
        """Test creating exception with original error for chaining."""
        original_error = ConnectionError("Connection refused")
        exception = SystemIntegrationError(
            "Database connection failed", original_error=original_error
        )

        assert exception.__cause__ is original_error
        assert exception.message == "Database connection failed"

    def test_constructor_with_partial_parameters(self):
        """Test creating exception with partial system/operation parameters."""
        # Only system
        exception1 = SystemIntegrationError(system="api")
        assert exception1.message == "External service integration failed"
        assert exception1.detail == "Check api service status and credentials"
        assert exception1.system == "api"
        assert exception1.operation is None

        # Only operation
        exception2 = SystemIntegrationError(operation="backup")
        assert exception2.message == "External service integration failed"
        assert (
            exception2.detail
            == "Check external service connectivity and authentication"
        )
        assert exception2.system is None
        assert exception2.operation == "backup"

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = SystemIntegrationError(
            message="Explicit integration error",
            system="elasticsearch",
            operation="index",
        )

        assert exception.message == "Explicit integration error"
        assert exception.system == "elasticsearch"
        assert exception.operation == "index"

    def test_custom_detail_overrides_generation(self):
        """Test that custom detail overrides generated detail."""
        exception = SystemIntegrationError(
            "Integration error", system="kafka", detail="Custom integration detail"
        )

        assert exception.detail == "Custom integration detail"
        assert exception.system == "kafka"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        original_error = TimeoutError("Request timeout")
        exception = SystemIntegrationError(
            message="Custom integration error",
            system="payment_gateway",
            operation="charge",
            detail="Custom detail",
            original_error=original_error,
        )

        assert exception.message == "Custom integration error"
        assert exception.system == "payment_gateway"
        assert exception.operation == "charge"
        assert exception.detail == "Custom detail"
        assert exception.__cause__ is original_error
        assert exception.status_code == 502


class TestOperationTimeoutError:
    """Test OperationTimeoutError class."""

    def test_inherits_from_base_system_exception(self):
        """Test that OperationTimeoutError inherits from BaseSystemException."""
        assert issubclass(OperationTimeoutError, BaseSystemException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = OperationTimeoutError("Custom timeout error")

        assert exception.message == "Custom timeout error"
        assert exception.status_code == 408
        assert (
            exception.detail == "Try again or contact support if the problem persists"
        )
        assert exception.operation is None
        assert exception.timeout_seconds is None

    def test_constructor_with_operation_generates_message(self):
        """Test that providing operation generates appropriate message."""
        exception = OperationTimeoutError(operation="file_upload")

        assert exception.message == "Operation timed out: file_upload"
        assert exception.operation == "file_upload"

    def test_constructor_without_message_or_operation(self):
        """Test creating exception without message or operation uses default."""
        exception = OperationTimeoutError()

        assert exception.message == "Operation took too long to complete"
        assert exception.status_code == 408
        assert exception.operation is None

    def test_constructor_with_timeout_seconds(self):
        """Test creating exception with timeout_seconds."""
        exception = OperationTimeoutError("Database query timeout", timeout_seconds=30)

        assert exception.timeout_seconds == 30
        assert exception.message == "Database query timeout"

    def test_constructor_with_operation_and_timeout(self):
        """Test creating exception with operation and timeout_seconds."""
        exception = OperationTimeoutError(
            operation="data_processing", timeout_seconds=120
        )

        assert exception.message == "Operation timed out: data_processing"
        assert exception.operation == "data_processing"
        assert exception.timeout_seconds == 120

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = OperationTimeoutError(
            message="Explicit timeout error", operation="backup"
        )

        assert exception.message == "Explicit timeout error"
        assert exception.operation == "backup"

    def test_fixed_detail_message(self):
        """Test that detail message is always fixed."""
        exceptions = [
            OperationTimeoutError("Custom message"),
            OperationTimeoutError(operation="test"),
            OperationTimeoutError(),
        ]

        for exception in exceptions:
            assert (
                exception.detail
                == "Try again or contact support if the problem persists"
            )

    def test_timeout_seconds_types(self):
        """Test timeout_seconds with different valid types."""
        test_values = [1, 30, 300, 3600]

        for timeout in test_values:
            exception = OperationTimeoutError("Timeout test", timeout_seconds=timeout)
            assert exception.timeout_seconds == timeout

    def test_status_code_is_408(self):
        """Test that status code is always 408."""
        exception = OperationTimeoutError("Any timeout message")

        assert exception.status_code == 408


class TestSystemResourceError:
    """Test SystemResourceError class."""

    def test_inherits_from_base_system_exception(self):
        """Test that SystemResourceError inherits from BaseSystemException."""
        assert issubclass(SystemResourceError, BaseSystemException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = SystemResourceError("Custom resource error")

        assert exception.message == "Custom resource error"
        assert exception.status_code == 503
        assert exception.detail == "Try again later when system load is lower"
        assert exception.resource_type is None

    def test_constructor_with_resource_type_generates_message(self):
        """Test that providing resource_type generates appropriate message."""
        exception = SystemResourceError(resource_type="memory")

        assert exception.message == "Insufficient memory available"
        assert exception.resource_type == "memory"

    def test_constructor_without_message_or_resource_type(self):
        """Test creating exception without message or resource_type uses default."""
        exception = SystemResourceError()

        assert exception.message == "System resources are insufficient"
        assert exception.status_code == 503
        assert exception.resource_type is None

    def test_constructor_with_custom_detail(self):
        """Test creating exception with custom detail."""
        custom_detail = "Wait for ongoing operations to complete"
        exception = SystemResourceError("Resource error", detail=custom_detail)

        assert exception.detail == custom_detail

    def test_constructor_with_resource_type_and_custom_detail(self):
        """Test creating exception with resource_type and custom detail."""
        exception = SystemResourceError(
            resource_type="disk_space", detail="Free up disk space and try again"
        )

        assert exception.message == "Insufficient disk_space available"
        assert exception.detail == "Free up disk space and try again"
        assert exception.resource_type == "disk_space"

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = SystemResourceError(
            message="Explicit resource error", resource_type="cpu"
        )

        assert exception.message == "Explicit resource error"
        assert exception.resource_type == "cpu"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = SystemResourceError(
            message="Custom resource error",
            resource_type="bandwidth",
            detail="Custom detail message",
        )

        assert exception.message == "Custom resource error"
        assert exception.resource_type == "bandwidth"
        assert exception.detail == "Custom detail message"
        assert exception.status_code == 503

    def test_default_detail_when_none_provided(self):
        """Test that default detail is set when none provided."""
        exception = SystemResourceError("Resource error")

        assert exception.detail == "Try again later when system load is lower"

    def test_status_code_is_503(self):
        """Test that status code is always 503."""
        exception = SystemResourceError("Any resource message")

        assert exception.status_code == 503

    def test_various_resource_types(self):
        """Test with various resource types."""
        resource_types = [
            "memory",
            "cpu",
            "disk_space",
            "bandwidth",
            "connections",
            "threads",
            "file_handles",
        ]

        for resource_type in resource_types:
            exception = SystemResourceError(resource_type=resource_type)
            assert exception.message == f"Insufficient {resource_type} available"
            assert exception.resource_type == resource_type


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance relationships."""

    def test_inheritance_chain(self):
        """Test the complete inheritance chain."""
        # BaseSystemException -> BaseAPIException -> Exception
        assert issubclass(BaseSystemException, BaseAPIException)
        assert issubclass(BaseAPIException, Exception)

        # All system exceptions inherit from BaseSystemException
        system_exception_classes = [
            SystemConfigurationError,
            SystemIntegrationError,
            OperationTimeoutError,
            SystemResourceError,
        ]

        for exc_class in system_exception_classes:
            assert issubclass(exc_class, BaseSystemException)
            assert issubclass(exc_class, BaseAPIException)

    def test_all_system_exceptions_can_be_caught_as_base_system_exception(self):
        """Test that all system exceptions can be caught as BaseSystemException."""
        exceptions = [
            SystemConfigurationError("Config error"),
            SystemIntegrationError("Integration error"),
            OperationTimeoutError("Timeout error"),
            SystemResourceError("Resource error"),
        ]

        for exc in exceptions:
            with pytest.raises(BaseSystemException):
                raise exc

    def test_status_codes_are_set_correctly(self):
        """Test that status codes are set correctly for each exception type."""
        # 500 for configuration errors
        config_error = SystemConfigurationError("Config error")
        assert config_error.status_code == 500

        # 502 for integration errors
        integration_error = SystemIntegrationError("Integration error")
        assert integration_error.status_code == 502

        # 408 for timeout errors
        timeout_error = OperationTimeoutError("Timeout error")
        assert timeout_error.status_code == 408

        # 503 for resource errors
        resource_error = SystemResourceError("Resource error")
        assert resource_error.status_code == 503

    def test_base_api_exception_attributes_preserved(self):
        """Test that BaseAPIException attributes are preserved."""
        exception = SystemConfigurationError("Test", setting="TEST_SETTING")

        # Should have BaseAPIException attributes
        assert hasattr(exception, "message")
        assert hasattr(exception, "status_code")
        assert hasattr(exception, "detail")
        assert hasattr(exception, "should_alert")

        # Should also have system-specific attributes
        assert hasattr(exception, "setting")

    def test_original_error_chaining_support(self):
        """Test that SystemIntegrationError supports original error chaining."""
        original_error = ValueError("Connection failed")
        exception = SystemIntegrationError(
            "Integration failed", original_error=original_error
        )

        assert exception.__cause__ is original_error


class TestExceptionIntegration:
    """Test integration scenarios and real-world usage patterns."""

    def test_exception_serialization_compatibility(self):
        """Test that exceptions work with string representation."""
        exceptions = [
            SystemConfigurationError("Config error"),
            SystemIntegrationError("Integration error"),
            OperationTimeoutError("Timeout error"),
            SystemResourceError("Resource error"),
        ]

        for exc in exceptions:
            assert str(exc) == exc.message
            assert repr(exc)  # Should not raise

    def test_exception_with_original_error_chaining(self):
        """Test exception chaining works with system exceptions."""
        try:
            raise ConnectionError("Database connection failed")
        except ConnectionError as original:
            system_exception = SystemIntegrationError(
                "Database integration failed",
                system="postgresql",
                operation="connect",
                original_error=original,
            )

            assert system_exception.__cause__ is original
            assert system_exception.system == "postgresql"
            assert system_exception.operation == "connect"

    def test_realistic_usage_scenarios(self):
        """Test realistic usage scenarios for each exception type."""
        # Configuration error scenario
        config_error = SystemConfigurationError(setting="DATABASE_URL")
        assert config_error.message == "Configuration error: DATABASE_URL"
        assert config_error.status_code == 500

        # Integration error scenario
        integration_error = SystemIntegrationError(
            system="payment_api", operation="charge_card"
        )
        assert (
            integration_error.message
            == "Unable to connect to payment_api for charge_card"
        )
        assert integration_error.status_code == 502

        # Timeout error scenario
        timeout_error = OperationTimeoutError(
            operation="large_file_upload", timeout_seconds=300
        )
        assert timeout_error.message == "Operation timed out: large_file_upload"
        assert timeout_error.timeout_seconds == 300
        assert timeout_error.status_code == 408

        # Resource error scenario
        resource_error = SystemResourceError(resource_type="memory")
        assert resource_error.message == "Insufficient memory available"
        assert resource_error.status_code == 503

    def test_exception_detail_messages_are_helpful(self):
        """Test that detail messages provide helpful information."""
        # Configuration error
        config_error = SystemConfigurationError("Config error")
        assert "configuration" in config_error.detail.lower()
        assert "environment" in config_error.detail.lower()

        # Integration error
        integration_error = SystemIntegrationError("Integration error", system="redis")
        assert "redis" in integration_error.detail.lower()
        assert "status" in integration_error.detail.lower()

        # Timeout error
        timeout_error = OperationTimeoutError("Timeout error")
        assert "try again" in timeout_error.detail.lower()

        # Resource error
        resource_error = SystemResourceError("Resource error")
        assert "try again later" in resource_error.detail.lower()

    def test_exception_attributes_are_accessible(self):
        """Test that custom attributes are accessible for monitoring/logging."""
        # Configuration error
        config_error = SystemConfigurationError(setting="API_KEY")
        assert config_error.setting == "API_KEY"

        # Integration error
        integration_error = SystemIntegrationError(system="database", operation="query")
        assert integration_error.system == "database"
        assert integration_error.operation == "query"

        # Timeout error
        timeout_error = OperationTimeoutError(operation="backup", timeout_seconds=3600)
        assert timeout_error.operation == "backup"
        assert timeout_error.timeout_seconds == 3600

        # Resource error
        resource_error = SystemResourceError(resource_type="cpu")
        assert resource_error.resource_type == "cpu"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
