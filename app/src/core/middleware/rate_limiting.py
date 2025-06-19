import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

API_KEY_LOG_PREFIX_LENGTH = 8


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
        self._lock = asyncio.Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        if not hasattr(request.state, "api_key") or not request.state.api_key:
            logger.debug("Request missing API key, skipping rate limit")
            return await call_next(request)
        if (
            not hasattr(request.state, "authenticated")
            or not request.state.authenticated
        ):
            logger.debug("Request not authenticated, skipping rate limit")
            return await call_next(request)

        api_key = request.state.api_key
        current_time = time.time()

        logger.debug(f"Rate limiting check for key: {api_key[:8]}...")

        async with self._lock:
            await self._cleanup_old_entries_async(current_time)

            requests = self.requests[api_key]
            while requests and current_time - requests[0] > self.window_seconds:
                requests.popleft()

            current_count = len(requests)
            logger.debug(
                f"Current request count for key {api_key[:8]}: "
                f"{current_count}/{self.requests_per_minute}"
            )

            if current_count >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for API key: {api_key[:8]}... "
                    f"({current_count}/{self.requests_per_minute})"
                )
                return JSONResponse(
                    content={
                        "error": "Rate limit exceeded",
                        "status_code": 429,
                        "detail": f"Maximum {self.requests_per_minute} "
                        "requests per minute allowed",
                    },
                    status_code=429,
                    headers={"Retry-After": str(self.window_seconds)},
                )

            requests.append(current_time)
            logger.debug(
                f"Request {current_count + 1}/{self.requests_per_minute} "
                f"for key {api_key[:8]}"
            )

        return await call_next(request)

    async def _cleanup_old_entries_async(self, current_time: float) -> None:
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
