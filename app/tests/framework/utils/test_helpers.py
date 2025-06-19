from contextlib import contextmanager
from datetime import datetime
from typing import Generator
from unittest.mock import patch


@contextmanager
def freeze_time(target_time: datetime) -> Generator[None, None, None]:
    with (
        patch("app.src.domain.date_service.datetime") as mock_dt,
        patch("datetime.datetime") as mock_datetime,
    ):
        mock_dt.now.return_value = target_time
        mock_datetime.now.return_value = target_time
        yield


def wait_for_condition(
    condition_func, timeout: float = 5.0, interval: float = 0.1
) -> bool:
    import time

    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False
