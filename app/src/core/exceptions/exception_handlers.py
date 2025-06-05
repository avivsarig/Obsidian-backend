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
    _add_error_schemas_to_openapi(app)

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


def _add_error_schemas_to_openapi(app: FastAPI) -> None:
    def enhanced_openapi_generator():
        if app.openapi_schema:
            return app.openapi_schema

        # Import here to avoid circular dependencies during app initialization
        from fastapi.openapi.utils import get_openapi

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        for path_data in openapi_schema.get("paths", {}).values():
            for method_data in path_data.values():
                if isinstance(method_data, dict) and "responses" in method_data:
                    _add_error_responses_to_endpoint(method_data["responses"])

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = enhanced_openapi_generator


def _add_error_responses_to_endpoint(responses: dict) -> None:
    # Import schemas here to avoid circular imports
    from app.src.core.exceptions.exception_schemas import (
        ServerErrorResponse,
        ValidationErrorResponse,
    )

    # Only add generic schemas if no specific error responses are defined
    if "400" not in responses:
        responses["400"] = {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": ValidationErrorResponse.model_json_schema()
                }
            },
        }

    if "500" not in responses:
        responses["500"] = {
            "description": "Internal Server Error",
            "content": {
                "application/json": {"schema": ServerErrorResponse.model_json_schema()}
            },
        }
