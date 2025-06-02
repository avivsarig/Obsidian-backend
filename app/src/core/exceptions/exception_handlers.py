import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.exception_responses import (
    create_api_error_response,
    create_server_error_response,
)
from app.src.core.middleware.request_tracking import get_request_id

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(
        request: Request, exc: BaseAPIException
    ) -> JSONResponse:
        logger.warning(
            f"API exception: {exc.message}",
            extra={
                "request_id": get_request_id(),
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
            },
            exc_info=exc if logger.isEnabledFor(logging.DEBUG) else None,
        )

        response_data = create_api_error_response(exc, request)

        return JSONResponse(
            status_code=exc.status_code,
            content=response_data,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        if isinstance(exc, BaseAPIException):
            return await api_exception_handler(request, exc)

        logger.error(
            "Unhandled exception occurred",
            extra={
                "request_id": get_request_id(),
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=exc,
        )

        response_data = create_server_error_response(exc, request)

        return JSONResponse(
            status_code=500,
            content=response_data,
        )
