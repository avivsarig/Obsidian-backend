from app.src.core.exceptions.base_exceptions import BaseAPIException


class BaseVaultException(BaseAPIException):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message,
            status_code=500,
            detail=detail,
            original_error=original_error,
        )


class VaultNotFoundError(BaseVaultException):
    def __init__(
        self,
        message: str | None = None,
        vault_path: str | None = None,
    ):
        if message is None and vault_path:
            message = f"Vault not found at path: {vault_path}"
        elif message is None:
            message = "Vault directory not found"

        super().__init__(
            message,
            detail="Check that the vault path is correctly configured and accessible",
        )
        self.vault_path = vault_path


class VaultFileOperationError(BaseVaultException):
    def __init__(
        self,
        message: str | None = None,
        operation: str | None = None,
        path: str | None = None,
        original_error: Exception | None = None,
    ):
        if message is None and operation and path:
            message = f"Unable to {operation} file at {path}"
        elif message is None:
            message = "File operation failed"

        super().__init__(
            message,
            detail="Check file permissions and disk space",
            original_error=original_error,
        )
        self.operation = operation
        self.path = path


class VaultGitOperationError(BaseVaultException):
    def __init__(
        self,
        message: str | None = None,
        operation: str | None = None,
        detail: str | None = None,
        original_error: Exception | None = None,
    ):
        if message is None and operation:
            message = f"Unable to sync with repository during {operation}"
        elif message is None:
            message = "Repository synchronization failed"

        if detail is None:
            detail = "Check repository status and network connectivity"

        super().__init__(
            message,
            detail=detail,
            original_error=original_error,
        )
        self.operation = operation


class VaultConcurrencyError(BaseVaultException):
    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
        resource: str | None = None,
        timeout_seconds: int | None = None,
    ):
        if message is None and resource:
            message = f"Resource is currently in use: {resource}"
        elif message is None:
            message = "Resource is locked by another operation"

        super().__init__(
            message,
            status_code=409,
            detail="Please try again in a moment",
        )
        self.resource = resource
        self.timeout_seconds = timeout_seconds
