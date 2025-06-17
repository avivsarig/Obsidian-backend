from app.src.core.exceptions.base_exceptions import BaseAPIException


class AuthenticationRequiredError(BaseAPIException):
    def __init__(
        self,
        message: str = "Authentication required",
    ):
        super().__init__(
            message=message,
            status_code=401,
            detail="Provide valid API key in Authorization header",
        )


class InvalidAPIKeyError(BaseAPIException):
    def __init__(
        self,
        message: str = "Invalid API key",
    ):
        super().__init__(
            message=message,
            status_code=401,
            detail="The provided API key is not valid",
        )
