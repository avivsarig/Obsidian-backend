from app.src.core.exceptions.base_exceptions import BaseAPIException


class BaseSystemException(BaseAPIException):
    pass


class SystemConfigurationError(BaseSystemException):
    def __init__(
        self,
        message: str | None = None,
        setting: str | None = None,
        detail: str | None = None,
    ):
        if message is None and setting:
            message = f"Configuration error: {setting}"
        elif message is None:
            message = "System configuration is invalid"

        if detail is None:
            detail = "Check application configuration and environment variables"

        super().__init__(
            message,
            status_code=500,
            detail=detail,
        )
        self.setting = setting


class SystemIntegrationError(BaseSystemException):
    def __init__(
        self,
        message: str | None = None,
        system: str | None = None,
        operation: str | None = None,
        detail: str | None = None,
        original_error: Exception | None = None,
    ):
        if message is None and system and operation:
            message = f"Unable to connect to {system} for {operation}"
        elif message is None:
            message = "External service integration failed"

        if detail is None and system:
            detail = f"Check {system} service status and credentials"
        elif detail is None:
            detail = "Check external service connectivity and authentication"

        super().__init__(
            message,
            status_code=502,
            detail=detail,
            original_error=original_error,
        )
        self.system = system
        self.operation = operation


class OperationTimeoutError(BaseSystemException):
    def __init__(
        self,
        message: str | None = None,
        operation: str | None = None,
        timeout_seconds: int | None = None,
    ):
        if message is None and operation:
            message = f"Operation timed out: {operation}"
        elif message is None:
            message = "Operation took too long to complete"

        super().__init__(
            message,
            status_code=408,
            detail="Try again or contact support if the problem persists",
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class SystemResourceError(BaseSystemException):
    def __init__(
        self,
        message: str | None = None,
        resource_type: str | None = None,
        detail: str | None = None,
    ):
        if message is None and resource_type:
            message = f"Insufficient {resource_type} available"
        elif message is None:
            message = "System resources are insufficient"

        if detail is None:
            detail = "Try again later when system load is lower"

        super().__init__(
            message,
            status_code=503,
            detail=detail,
        )
        self.resource_type = resource_type
