import logging
import time
from collections import defaultdict, deque
from typing import Callable, Deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 1000,
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
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        self._cleanup_old_entries(current_time)

        requests = self.requests[client_ip]
        while requests and current_time - requests[0] > self.window_seconds:
            requests.popleft()

        if len(requests) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)},
            )

        requests.append(current_time)
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded: str | None = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        client_host = request.client.host if request.client else None
        return client_host or "unknown"

    def _cleanup_old_entries(self, current_time: float) -> None:
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = current_time - self.window_seconds
        empty_ips = [
            ip
            for ip, requests in self.requests.items()
            if not requests or requests[-1] < cutoff
        ]

        for ip in empty_ips:
            del self.requests[ip]

        self.last_cleanup = current_time

        if empty_ips:
            logger.debug(f"Cleaned up {len(empty_ips)} inactive IP entries")
