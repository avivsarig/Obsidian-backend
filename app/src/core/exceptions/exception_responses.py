from typing import Any

from fastapi import Request

from app.src.core.config import get_settings
from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.middleware.request_tracking import get_request_id
from app.src.core.monitoring.alerts import send_alert_if_needed

settings = get_settings()


def create_api_error_response(
    exc: BaseAPIException,
    request: Request,
) -> dict[str, Any]:
    request_id = get_request_id()

    response = {
        "error": exc.message,
        "status_code": exc.status_code,
        "request_id": request_id,
    }

    if exc.detail:
        response["detail"] = exc.detail

    if settings.environment == "development":
        response.update(
            {
                "path": str(request.url.path),
                "method": request.method,
            }
        )

        if exc.__cause__:
            response["original_error"] = {
                "type": type(exc.__cause__).__name__,
                "message": str(exc.__cause__),
            }

    send_alert_if_needed(exc, request, request_id)

    return response


def create_server_error_response(
    exc: Exception,
    request: Request,
) -> dict[str, Any]:
    request_id = get_request_id()

    response = {
        "error": "Internal server error",
        "status_code": 500,
        "request_id": request_id,
        "detail": "An unexpected error occurred. Please try again.",
    }

    if settings.environment == "development":
        response.update(
            {
                "path": str(request.url.path),
                "method": request.method,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }
        )

    return response
