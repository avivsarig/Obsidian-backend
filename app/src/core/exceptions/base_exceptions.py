class BaseAPIException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: str | None = None,
        original_error: Exception | None = None,
        should_alert: bool = False,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.should_alert = should_alert

        if original_error:
            self.__cause__ = original_error

        super().__init__(self.message)
