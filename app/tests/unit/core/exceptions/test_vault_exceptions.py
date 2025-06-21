import pytest

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.vault_exceptions import (
    BaseVaultException,
    VaultConcurrencyError,
    VaultFileOperationError,
    VaultGitOperationError,
    VaultNotFoundError,
)


class TestBaseVaultException:
    """Test BaseVaultException class."""

    def test_inherits_from_base_api_exception(self):
        """Test that BaseVaultException inherits from BaseAPIException."""
        assert issubclass(BaseVaultException, BaseAPIException)

    def test_can_be_instantiated(self):
        """Test that BaseVaultException can be instantiated."""
        exception = BaseVaultException("Test vault exception")

        assert isinstance(exception, BaseVaultException)
        assert isinstance(exception, BaseAPIException)
        assert exception.message == "Test vault exception"

    def test_status_code_respects_parameter(self):
        """Test that status code respects the parameter passed."""
        # Default should be 500
        exception1 = BaseVaultException("Test")
        assert exception1.status_code == 500

        # Custom status code should be respected
        exception2 = BaseVaultException("Test", status_code=404)
        assert exception2.status_code == 404

    def test_constructor_with_detail(self):
        """Test creating exception with detail."""
        exception = BaseVaultException("Test", detail="Custom detail")

        assert exception.detail == "Custom detail"

    def test_constructor_with_original_error(self):
        """Test creating exception with original error for chaining."""
        original_error = OSError("File not found")
        exception = BaseVaultException("Test", original_error=original_error)

        assert exception.__cause__ is original_error

    def test_constructor_with_all_parameters(self):
        """Test creating exception with all parameters."""
        original_error = PermissionError("Access denied")
        exception = BaseVaultException(
            "Custom vault error",
            status_code=422,  # This should be respected now
            detail="Custom detail",
            original_error=original_error,
        )

        assert exception.message == "Custom vault error"
        assert exception.status_code == 422  # Should be the value passed
        assert exception.detail == "Custom detail"
        assert exception.__cause__ is original_error

    def test_can_be_raised_and_caught(self):
        """Test that BaseVaultException can be raised and caught."""
        with pytest.raises(BaseVaultException) as exc_info:
            raise BaseVaultException("Test raising")

        assert exc_info.value.message == "Test raising"

    def test_can_be_caught_as_base_api_exception(self):
        """Test that BaseVaultException can be caught as BaseAPIException."""
        with pytest.raises(BaseAPIException) as exc_info:
            raise BaseVaultException("Test base catching")

        assert isinstance(exc_info.value, BaseVaultException)


class TestVaultNotFoundError:
    """Test VaultNotFoundError class."""

    def test_inherits_from_base_vault_exception(self):
        """Test that VaultNotFoundError inherits from BaseVaultException."""
        assert issubclass(VaultNotFoundError, BaseVaultException)
        assert issubclass(VaultNotFoundError, BaseAPIException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = VaultNotFoundError("Custom vault not found message")

        assert exception.message == "Custom vault not found message"
        assert exception.status_code == 500
        assert (
            exception.detail
            == "Check that the vault path is correctly configured and accessible"
        )
        assert exception.vault_path is None

    def test_constructor_with_vault_path_generates_message(self):
        """Test that providing vault_path generates appropriate message."""
        exception = VaultNotFoundError(vault_path="/path/to/vault")

        assert exception.message == "Vault not found at path: /path/to/vault"
        assert exception.vault_path == "/path/to/vault"

    def test_constructor_without_message_or_vault_path(self):
        """Test creating exception without message or vault_path uses default."""
        exception = VaultNotFoundError()

        assert exception.message == "Vault directory not found"
        assert exception.status_code == 500
        assert exception.vault_path is None

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = VaultNotFoundError(
            message="Explicit vault message", vault_path="/some/path"
        )

        assert exception.message == "Explicit vault message"
        assert exception.vault_path == "/some/path"

    def test_fixed_detail_message(self):
        """Test that detail message is always fixed."""
        exceptions = [
            VaultNotFoundError("Custom message"),
            VaultNotFoundError(vault_path="/test/path"),
            VaultNotFoundError(),
        ]

        expected_detail = (
            "Check that the vault path is correctly configured and accessible"
        )
        for exception in exceptions:
            assert exception.detail == expected_detail

    def test_various_vault_paths(self):
        """Test with various vault path formats."""
        vault_paths = [
            "/absolute/path/to/vault",
            "relative/path/vault",
            "/home/user/Documents/MyVault",
            "C:\\Users\\User\\Vault",
            "/mnt/storage/obsidian",
        ]

        for path in vault_paths:
            exception = VaultNotFoundError(vault_path=path)
            assert exception.message == f"Vault not found at path: {path}"
            assert exception.vault_path == path


class TestVaultFileOperationError:
    """Test VaultFileOperationError class."""

    def test_inherits_from_base_vault_exception(self):
        """Test that VaultFileOperationError inherits from BaseVaultException."""
        assert issubclass(VaultFileOperationError, BaseVaultException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = VaultFileOperationError("Custom file operation error")

        assert exception.message == "Custom file operation error"
        assert exception.status_code == 500
        assert exception.detail == "Check file permissions and disk space"
        assert exception.operation is None
        assert exception.path is None

    def test_constructor_with_operation_and_path_generates_message(self):
        """Test that providing operation and path generates appropriate message."""
        exception = VaultFileOperationError(operation="read", path="/vault/note.md")

        assert exception.message == "Unable to read file at /vault/note.md"
        assert exception.operation == "read"
        assert exception.path == "/vault/note.md"

    def test_constructor_without_message_operation_or_path(self):
        """Test creating exception without message, operation, or path uses default."""
        exception = VaultFileOperationError()

        assert exception.message == "File operation failed"
        assert exception.status_code == 500
        assert exception.operation is None
        assert exception.path is None

    def test_constructor_with_original_error(self):
        """Test creating exception with original error for chaining."""
        original_error = PermissionError("Permission denied")
        exception = VaultFileOperationError(
            "File access failed", original_error=original_error
        )

        assert exception.__cause__ is original_error
        assert exception.message == "File access failed"

    def test_constructor_with_partial_parameters(self):
        """Test creating exception with partial operation/path parameters."""
        # Only operation
        exception1 = VaultFileOperationError(operation="write")
        assert exception1.message == "File operation failed"
        assert exception1.operation == "write"
        assert exception1.path is None

        # Only path
        exception2 = VaultFileOperationError(path="/vault/file.md")
        assert exception2.message == "File operation failed"
        assert exception2.operation is None
        assert exception2.path == "/vault/file.md"

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = VaultFileOperationError(
            message="Explicit file error", operation="delete", path="/vault/temp.md"
        )

        assert exception.message == "Explicit file error"
        assert exception.operation == "delete"
        assert exception.path == "/vault/temp.md"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        original_error = OSError("Disk full")
        exception = VaultFileOperationError(
            message="Custom file operation error",
            operation="write",
            path="/vault/large_file.md",
            original_error=original_error,
        )

        assert exception.message == "Custom file operation error"
        assert exception.operation == "write"
        assert exception.path == "/vault/large_file.md"
        assert exception.__cause__ is original_error
        assert exception.status_code == 500

    def test_fixed_detail_message(self):
        """Test that detail message is always fixed."""
        exception = VaultFileOperationError("Test error")

        assert exception.detail == "Check file permissions and disk space"

    def test_various_operations_and_paths(self):
        """Test with various operation types and file paths."""
        test_cases = [
            ("read", "/vault/notes/daily/2023-01-01.md"),
            ("write", "/vault/templates/template.md"),
            ("delete", "/vault/archive/old_note.md"),
            ("move", "/vault/inbox/new_note.md"),
            ("copy", "/vault/attachments/image.png"),
        ]

        for operation, path in test_cases:
            exception = VaultFileOperationError(operation=operation, path=path)
            assert exception.message == f"Unable to {operation} file at {path}"
            assert exception.operation == operation
            assert exception.path == path


class TestVaultGitOperationError:
    """Test VaultGitOperationError class."""

    def test_inherits_from_base_vault_exception(self):
        """Test that VaultGitOperationError inherits from BaseVaultException."""
        assert issubclass(VaultGitOperationError, BaseVaultException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = VaultGitOperationError("Custom git operation error")

        assert exception.message == "Custom git operation error"
        assert exception.status_code == 500
        assert exception.detail == "Check repository status and network connectivity"
        assert exception.operation is None

    def test_constructor_with_operation_generates_message(self):
        """Test that providing operation generates appropriate message."""
        exception = VaultGitOperationError(operation="pull")

        assert exception.message == "Unable to sync with repository during pull"
        assert exception.operation == "pull"

    def test_constructor_without_message_or_operation(self):
        """Test creating exception without message or operation uses default."""
        exception = VaultGitOperationError()

        assert exception.message == "Repository synchronization failed"
        assert exception.status_code == 500
        assert exception.operation is None

    def test_constructor_with_custom_detail(self):
        """Test creating exception with custom detail."""
        custom_detail = "Repository is behind remote by 5 commits"
        exception = VaultGitOperationError("Git error", detail=custom_detail)

        assert exception.detail == custom_detail

    def test_constructor_with_original_error(self):
        """Test creating exception with original error for chaining."""
        original_error = ConnectionError("Network timeout")
        exception = VaultGitOperationError(
            "Git sync failed", original_error=original_error
        )

        assert exception.__cause__ is original_error
        assert exception.message == "Git sync failed"

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = VaultGitOperationError(
            message="Explicit git error", operation="push"
        )

        assert exception.message == "Explicit git error"
        assert exception.operation == "push"

    def test_default_detail_when_none_provided(self):
        """Test that default detail is set when none provided."""
        exception = VaultGitOperationError("Git error")

        assert exception.detail == "Check repository status and network connectivity"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        original_error = Exception("Authentication failed")
        exception = VaultGitOperationError(
            message="Custom git operation error",
            operation="fetch",
            detail="Custom git detail",
            original_error=original_error,
        )

        assert exception.message == "Custom git operation error"
        assert exception.operation == "fetch"
        assert exception.detail == "Custom git detail"
        assert exception.__cause__ is original_error
        assert exception.status_code == 500

    def test_various_git_operations(self):
        """Test with various git operation types."""
        git_operations = [
            "pull",
            "push",
            "fetch",
            "commit",
            "merge",
            "clone",
            "checkout",
        ]

        for operation in git_operations:
            exception = VaultGitOperationError(operation=operation)
            assert (
                exception.message
                == f"Unable to sync with repository during {operation}"
            )
            assert exception.operation == operation


class TestVaultConcurrencyError:
    """Test VaultConcurrencyError class."""

    def test_inherits_from_base_vault_exception(self):
        """Test that VaultConcurrencyError inherits from BaseVaultException."""
        assert issubclass(VaultConcurrencyError, BaseVaultException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = VaultConcurrencyError("Custom concurrency error")

        assert exception.message == "Custom concurrency error"
        assert exception.status_code == 409
        assert exception.detail == "Please try again in a moment"
        assert exception.resource is None
        assert exception.timeout_seconds is None

    def test_constructor_with_resource_generates_message(self):
        """Test that providing resource generates appropriate message."""
        exception = VaultConcurrencyError(resource="notes/daily/2023-01-01.md")

        assert (
            exception.message
            == "Resource is currently in use: notes/daily/2023-01-01.md"
        )
        assert exception.resource == "notes/daily/2023-01-01.md"

    def test_constructor_without_message_or_resource(self):
        """Test creating exception without message or resource uses default."""
        exception = VaultConcurrencyError()

        assert exception.message == "Resource is locked by another operation"
        assert exception.status_code == 409
        assert exception.resource is None

    def test_constructor_with_timeout_seconds(self):
        """Test creating exception with timeout_seconds."""
        exception = VaultConcurrencyError("Lock timeout", timeout_seconds=30)

        assert exception.timeout_seconds == 30
        assert exception.message == "Lock timeout"

    def test_constructor_with_resource_and_timeout(self):
        """Test creating exception with both resource and timeout_seconds."""
        exception = VaultConcurrencyError(resource="vault.db", timeout_seconds=60)

        assert exception.message == "Resource is currently in use: vault.db"
        assert exception.resource == "vault.db"
        assert exception.timeout_seconds == 60

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = VaultConcurrencyError(
            message="Explicit concurrency error", resource="locked_file.md"
        )

        assert exception.message == "Explicit concurrency error"
        assert exception.resource == "locked_file.md"

    def test_status_code_is_409(self):
        """Test that status code is always 409 for concurrency errors."""
        exception = VaultConcurrencyError("Any concurrency message")

        assert exception.status_code == 409

    def test_fixed_detail_message_overrides_custom_detail(self):
        """Test that detail is always fixed and overrides custom detail."""
        # Custom detail parameter is not supported in this exception
        exception = VaultConcurrencyError("Concurrency error")

        assert exception.detail == "Please try again in a moment"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = VaultConcurrencyError(
            message="Custom concurrency error",
            detail="This parameter is ignored",  # Not used in this exception
            resource="shared_resource.md",
            timeout_seconds=120,
        )

        assert exception.message == "Custom concurrency error"
        assert exception.resource == "shared_resource.md"
        assert exception.timeout_seconds == 120
        # Detail should still be the fixed message
        assert exception.detail == "Please try again in a moment"

    def test_various_resource_types(self):
        """Test with various resource types."""
        resources = [
            "vault.db",
            "notes/important.md",
            "attachments/large_file.pdf",
            ".obsidian/workspace",
            "templates/daily_template.md",
        ]

        for resource in resources:
            exception = VaultConcurrencyError(resource=resource)
            assert exception.message == f"Resource is currently in use: {resource}"
            assert exception.resource == resource


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance relationships."""

    def test_inheritance_chain(self):
        """Test the complete inheritance chain."""
        # BaseVaultException -> BaseAPIException -> Exception
        assert issubclass(BaseVaultException, BaseAPIException)
        assert issubclass(BaseAPIException, Exception)

        # All vault exceptions inherit from BaseVaultException
        vault_exception_classes = [
            VaultNotFoundError,
            VaultFileOperationError,
            VaultGitOperationError,
            VaultConcurrencyError,
        ]

        for exc_class in vault_exception_classes:
            assert issubclass(exc_class, BaseVaultException)
            assert issubclass(exc_class, BaseAPIException)

    def test_all_vault_exceptions_can_be_caught_as_base_vault_exception(self):
        """Test that all vault exceptions can be caught as BaseVaultException."""
        exceptions = [
            VaultNotFoundError("Not found"),
            VaultFileOperationError("File error"),
            VaultGitOperationError("Git error"),
            VaultConcurrencyError("Concurrency error"),
        ]

        for exc in exceptions:
            with pytest.raises(BaseVaultException):
                raise exc

    def test_status_codes_are_set_correctly(self):
        """Test that status codes are set correctly for each exception type."""
        # 500 for most vault errors
        not_found = VaultNotFoundError("Not found")
        assert not_found.status_code == 500

        file_error = VaultFileOperationError("File error")
        assert file_error.status_code == 500

        git_error = VaultGitOperationError("Git error")
        assert git_error.status_code == 500

        # 409 for concurrency errors
        concurrency_error = VaultConcurrencyError("Concurrency error")
        assert concurrency_error.status_code == 409

    def test_base_api_exception_attributes_preserved(self):
        """Test that BaseAPIException attributes are preserved."""
        exception = VaultNotFoundError("Test", vault_path="/test/vault")

        # Should have BaseAPIException attributes
        assert hasattr(exception, "message")
        assert hasattr(exception, "status_code")
        assert hasattr(exception, "detail")
        assert hasattr(exception, "should_alert")

        # Should also have vault-specific attributes
        assert hasattr(exception, "vault_path")

    def test_original_error_chaining_support(self):
        """Test that vault exceptions support original error chaining."""
        original_error = FileNotFoundError("File not found")

        # BaseVaultException supports it directly
        base_exception = BaseVaultException("Base error", original_error=original_error)
        assert base_exception.__cause__ is original_error

        # VaultFileOperationError supports it
        file_exception = VaultFileOperationError(
            "File error", original_error=original_error
        )
        assert file_exception.__cause__ is original_error

        # VaultGitOperationError supports it
        git_exception = VaultGitOperationError(
            "Git error", original_error=original_error
        )
        assert git_exception.__cause__ is original_error


class TestExceptionIntegration:
    """Test integration scenarios and real-world usage patterns."""

    def test_exception_serialization_compatibility(self):
        """Test that exceptions work with string representation."""
        exceptions = [
            VaultNotFoundError("Vault not found"),
            VaultFileOperationError("File operation failed"),
            VaultGitOperationError("Git operation failed"),
            VaultConcurrencyError("Concurrency error"),
        ]

        for exc in exceptions:
            assert str(exc) == exc.message
            assert repr(exc)  # Should not raise

    def test_exception_with_original_error_chaining(self):
        """Test exception chaining works with vault exceptions."""
        try:
            raise OSError("Permission denied")
        except OSError as original:
            vault_exception = VaultFileOperationError(
                "Unable to write vault file",
                operation="write",
                path="/vault/notes/new_note.md",
                original_error=original,
            )

            assert vault_exception.__cause__ is original
            assert vault_exception.operation == "write"
            assert vault_exception.path == "/vault/notes/new_note.md"

    def test_realistic_usage_scenarios(self):
        """Test realistic usage scenarios for each exception type."""
        # Vault not found scenario
        vault_not_found = VaultNotFoundError(vault_path="/Users/john/Documents/MyVault")
        assert (
            vault_not_found.message
            == "Vault not found at path: /Users/john/Documents/MyVault"
        )
        assert vault_not_found.status_code == 500

        # File operation scenario
        file_error = VaultFileOperationError(
            operation="read", path="/vault/notes/important.md"
        )
        assert file_error.message == "Unable to read file at /vault/notes/important.md"
        assert file_error.status_code == 500

        # Git operation scenario
        git_error = VaultGitOperationError(operation="pull")
        assert git_error.message == "Unable to sync with repository during pull"
        assert git_error.status_code == 500

        # Concurrency scenario
        concurrency_error = VaultConcurrencyError(
            resource="notes/daily/2023-01-01.md", timeout_seconds=30
        )
        assert (
            concurrency_error.message
            == "Resource is currently in use: notes/daily/2023-01-01.md"
        )
        assert concurrency_error.timeout_seconds == 30
        assert concurrency_error.status_code == 409

    def test_exception_detail_messages_are_helpful(self):
        """Test that detail messages provide helpful information."""
        # Vault not found
        vault_not_found = VaultNotFoundError("Vault error")
        assert "vault path" in vault_not_found.detail.lower()
        assert "configured" in vault_not_found.detail.lower()

        # File operation
        file_error = VaultFileOperationError("File error")
        assert "permissions" in file_error.detail.lower()
        assert "disk space" in file_error.detail.lower()

        # Git operation
        git_error = VaultGitOperationError("Git error")
        assert "repository" in git_error.detail.lower()
        assert "connectivity" in git_error.detail.lower()

        # Concurrency
        concurrency_error = VaultConcurrencyError("Concurrency error")
        assert "try again" in concurrency_error.detail.lower()

    def test_exception_attributes_are_accessible(self):
        """Test that custom attributes are accessible for monitoring/logging."""
        # Vault not found
        vault_not_found = VaultNotFoundError(vault_path="/test/vault")
        assert vault_not_found.vault_path == "/test/vault"

        # File operation
        file_error = VaultFileOperationError(operation="write", path="/test/file.md")
        assert file_error.operation == "write"
        assert file_error.path == "/test/file.md"

        # Git operation
        git_error = VaultGitOperationError(operation="push")
        assert git_error.operation == "push"

        # Concurrency
        concurrency_error = VaultConcurrencyError(
            resource="locked_file.md", timeout_seconds=60
        )
        assert concurrency_error.resource == "locked_file.md"
        assert concurrency_error.timeout_seconds == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
