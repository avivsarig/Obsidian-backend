import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.src.core.auth.api_key_service import APIKeyService
from app.src.core.auth.exceptions import AuthenticationRequiredError, InvalidAPIKeyError

logger = logging.getLogger(__name__)

DEFAULT_EXEMPT_PATHS = frozenset(
    {
        "/api/v1/health",
        "/docs",
        "/redoc",
    }
)
AUTH_HEADER_NAME = "Authorization"
BEARER_PREFIX = "Bearer "


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        api_key_service: APIKeyService,
        exempt_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.api_key_service = api_key_service
        self.exempt_paths = exempt_paths or DEFAULT_EXEMPT_PATHS

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[
            [Request],
            JSONResponse,
        ],
    ) -> JSONResponse:
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        try:
            api_key = self._extract_api_key(request)
            is_valid = await self.api_key_service.validate_key(api_key)

            if not is_valid:
                raise InvalidAPIKeyError("Invalid API key provided")

            request.state.api_key = api_key
            request.state.authenticated = True

            return await call_next(request)

        except (AuthenticationRequiredError, InvalidAPIKeyError) as e:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Authentication failed for {client_ip}: {e.message}")

            return JSONResponse(
                content={"error": e.message, "status_code": e.status_code},
                status_code=e.status_code,
            )

    def _is_exempt_path(self, path: str) -> bool:
        return path in self.exempt_paths

    def _extract_api_key(self, request: Request) -> str:
        auth_header: str | None = request.headers.get(AUTH_HEADER_NAME)

        if not auth_header:
            raise AuthenticationRequiredError("Missing Authorization header")

        if not auth_header.startswith(BEARER_PREFIX):
            raise AuthenticationRequiredError("Invalid Authorization header format")

        api_key = auth_header[len(BEARER_PREFIX) :].strip()

        if not api_key:
            raise AuthenticationRequiredError("Empty API key")

        return api_key
