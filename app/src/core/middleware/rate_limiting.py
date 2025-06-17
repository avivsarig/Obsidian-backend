import logging
import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

LOG_KEY_PREFIX_LENGTH = 8


class PerKeyRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 100,
        window_seconds: int = 60,
        cleanup_interval: int = 300,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        self.requests: defaultdict[str, Deque[float]] = defaultdict(deque)
        self.last_cleanup = time.time()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        api_key = request.state.api_key
        current_time = time.time()

        self._cleanup_old_entries(current_time)

        requests = self.requests[api_key]
        while requests and current_time - requests[0] > self.window_seconds:
            requests.popleft()

        if len(requests) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for API key: {api_key[:LOG_KEY_PREFIX_LENGTH]}..."
            )
            return JSONResponse(
                content={
                    "error": "Rate limit exceeded",
                    "status_code": 429,
                    "detail": f"Maximum {self.requests_per_minute}"
                    "requests per minute allowed",
                },
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)},
            )

        requests.append(current_time)
        return await call_next(request)

    def _cleanup_old_entries(self, current_time: float) -> None:
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = current_time - self.window_seconds
        empty_keys = [
            key
            for key, requests in self.requests.items()
            if not requests or requests[-1] < cutoff
        ]

        for key in empty_keys:
            del self.requests[key]

        self.last_cleanup = current_time

        if empty_keys:
            logger.debug(f"Cleaned up {len(empty_keys)} inactive API key entries")
