import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Retrier:
    """A retry mechanism with exponential backoff for operations that may fail."""

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
    ) -> None:
        """Initialize the Retrier.

        Args:
            max_attempts: Maximum number of retry attempts (must be >= 1)
            base_delay: Base delay in seconds for exponential backoff (must be >= 0)
            max_delay: Maximum delay in seconds (must be >= base_delay)

        Raises:
            ValueError: If parameters are invalid
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:
        """Execute an operation with retry logic.

        Args:
            operation: A callable that returns a value or raises an exception

        Returns:
            The result of the successful operation

        Raises:
            The last exception encountered if all attempts fail
        """
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
                time.sleep(delay)

        if last_error is None:
            raise RuntimeError(
                "All retry attempts failed, but no exception was captured"
            )
        raise last_error
