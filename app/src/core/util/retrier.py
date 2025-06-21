import logging
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Retrier:
    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:
        last_error = None

        for attempt in range(self.max_attempts):
            try:
                return operation()
            except Exception as e:
                last_error = e
                # if last attempt, do not wait
                if attempt == self.max_attempts - 1:
                    break

                delay = min(
                    self.base_delay * (2**attempt),
                    self.max_delay,
                )
                logger.debug(
                    f"Attempt {attempt + 1} failed, retrying in {delay} seconds"
                )

        if last_error is None:
            raise RuntimeError("All retry attempt fail, but no exception was captured")
        raise last_error
