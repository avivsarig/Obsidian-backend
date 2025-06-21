from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.exception_handlers import (
    _add_error_responses_to_endpoint,
    _add_error_schemas_to_openapi,
    setup_exception_handlers,
)


class TestSetupExceptionHandlers:
    """Test the main setup_exception_handlers function."""

    def test_setup_exception_handlers_registers_handlers(self):
        """Test that setup_exception_handlers registers exception handlers."""
        mock_app = Mock(spec=FastAPI)
        mock_app.exception_handler = Mock(return_value=lambda f: f)

        setup_exception_handlers(mock_app)

        # Verify exception handlers were registered
        assert mock_app.exception_handler.call_count == 2

        # Check the exception types that were registered
        call_args = [call[0][0] for call in mock_app.exception_handler.call_args_list]
        assert BaseAPIException in call_args
        assert Exception in call_args

    def test_setup_exception_handlers_calls_openapi_enhancement(self):
        """Test that setup_exception_handlers enhances OpenAPI schemas."""
        mock_app = Mock(spec=FastAPI)
        mock_app.exception_handler = Mock(return_value=lambda f: f)

        with patch(
            "app.src.core.exceptions.exception_handlers._add_error_schemas_to_openapi"
        ) as mock_add_schemas:
            setup_exception_handlers(mock_app)
            mock_add_schemas.assert_called_once_with(mock_app)


class TestAPIExceptionHandler:
    """Test the BaseAPIException handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/test/path"
        request.method = "GET"
        return request

    @pytest.fixture
    def mock_exception(self):
        """Create a mock BaseAPIException."""
        return BaseAPIException(
            message="Test error message", status_code=400, detail="Test error detail"
        )

    @pytest.mark.asyncio
    async def test_api_exception_handler_basic_functionality(
        self, mock_request, mock_exception
    ):
        """Test basic API exception handler functionality."""
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler

        # Setup the handlers
        setup_exception_handlers(mock_app)

        # Get the registered handler function
        api_handler = handler_registry[BaseAPIException]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "test-request-id"
            mock_create_response.return_value = {"error": "test response"}

            result = await api_handler(mock_request, mock_exception)

            # Verify logging was called
            mock_logger.warning.assert_called_once()

            # Verify response creation was called
            mock_create_response.assert_called_once_with(mock_exception, mock_request)

            # Verify JSONResponse creation
            assert isinstance(result, JSONResponse)
            assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_api_exception_handler_logging_details(
        self, mock_request, mock_exception
    ):
        """Test that API exception handler logs correct details."""
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler

        setup_exception_handlers(mock_app)
        api_handler = handler_registry[BaseAPIException]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "test-request-id"
            mock_create_response.return_value = {"error": "test response"}
            mock_logger.isEnabledFor.return_value = False

            await api_handler(mock_request, mock_exception)

            # Verify logging call details
            mock_logger.warning.assert_called_once_with(
                f"API exception: {mock_exception.message}",
                extra={
                    "request_id": "test-request-id",
                    "exception_type": "BaseAPIException",
                    "path": "/test/path",
                    "method": "GET",
                    "status_code": 400,
                },
                exc_info=None,
            )

    @pytest.mark.asyncio
    async def test_api_exception_handler_debug_logging(
        self, mock_request, mock_exception
    ):
        """
        Test that API exception handler includes exc_info when debug logging is enabled.
        """
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler

        setup_exception_handlers(mock_app)
        api_handler = handler_registry[BaseAPIException]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "test-request-id"
            mock_create_response.return_value = {"error": "test response"}
            mock_logger.isEnabledFor.return_value = True  # Enable debug logging

            await api_handler(mock_request, mock_exception)

            # Verify exc_info is included when debug is enabled
            call_args = mock_logger.warning.call_args
            assert call_args[1]["exc_info"] is mock_exception

    @pytest.mark.asyncio
    async def test_api_exception_handler_different_status_codes(self, mock_request):
        """Test API exception handler with different status codes."""
        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (422, "Unprocessable Entity"),
        ]

        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler
        setup_exception_handlers(mock_app)
        api_handler = handler_registry[BaseAPIException]

        for status_code, message in test_cases:
            exception = BaseAPIException(message, status_code=status_code)

            with (
                patch("app.src.core.exceptions.exception_handlers.logger"),
                patch("app.src.core.exceptions.exception_handlers.get_request_id"),
                patch(
                    "app.src.core.exceptions.exception_handlers."
                    "create_api_error_response"
                ) as mock_create_response,
            ):
                mock_create_response.return_value = {"error": message}

                result = await api_handler(mock_request, exception)

                assert result.status_code == status_code


class TestGeneralExceptionHandler:
    """Test the general Exception handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/test/path"
        request.method = "POST"
        return request

    @pytest.mark.asyncio
    async def test_general_exception_handler_with_non_api_exception(self, mock_request):
        """Test general exception handler with non-BaseAPIException."""
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler
        setup_exception_handlers(mock_app)
        general_handler = handler_registry[Exception]

        test_exception = ValueError("Test value error")

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers."
                "create_server_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "test-request-id"
            mock_create_response.return_value = {"error": "Internal server error"}

            result = await general_handler(mock_request, test_exception)

            # Verify error logging
            mock_logger.error.assert_called_once_with(
                "Unhandled exception occurred",
                extra={
                    "request_id": "test-request-id",
                    "exception_type": "ValueError",
                    "path": "/test/path",
                    "method": "POST",
                },
                exc_info=test_exception,
            )

            # Verify response
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500
            mock_create_response.assert_called_once_with(test_exception, mock_request)

    @pytest.mark.asyncio
    async def test_general_exception_handler_delegates_base_api_exception(
        self, mock_request
    ):
        """Test that general handler delegates BaseAPIException to API handler."""
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler
        setup_exception_handlers(mock_app)

        general_handler = handler_registry[Exception]

        base_api_exception = BaseAPIException("Test API error", status_code=422)

        # Mock the necessary dependencies for the api handler
        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "test-request-id"
            mock_create_response.return_value = {"error": "test response"}

            result = await general_handler(mock_request, base_api_exception)

            # Verify delegation occurred by checking the result is a
            # JSONResponse with 422 status
            assert isinstance(result, JSONResponse)
            assert result.status_code == 422

            # Verify the API handler was called (indirectly through logging)
            mock_logger.warning.assert_called_once()
            mock_create_response.assert_called_once_with(
                base_api_exception, mock_request
            )

    @pytest.mark.asyncio
    async def test_general_exception_handler_different_exception_types(
        self, mock_request
    ):
        """Test general exception handler with various exception types."""
        exception_types = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
        ]

        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler
        setup_exception_handlers(mock_app)
        general_handler = handler_registry[Exception]

        for exception in exception_types:
            with (
                patch(
                    "app.src.core.exceptions.exception_handlers.logger"
                ) as mock_logger,
                patch("app.src.core.exceptions.exception_handlers.get_request_id"),
                patch(
                    "app.src.core.exceptions.exception_handlers."
                    "create_server_error_response"
                ) as mock_create_response,
            ):
                mock_create_response.return_value = {"error": "Server error"}

                result = await general_handler(mock_request, exception)

                # Verify logging includes correct exception type
                call_args = mock_logger.error.call_args
                assert (
                    call_args[1]["extra"]["exception_type"] == type(exception).__name__
                )
                assert call_args[1]["exc_info"] is exception

                # All unhandled exceptions return 500
                assert result.status_code == 500


class TestOpenAPIEnhancement:
    """Test OpenAPI schema enhancement functions."""

    def test_add_error_schemas_to_openapi_sets_custom_generator(self):
        """Test that _add_error_schemas_to_openapi sets a custom openapi generator."""
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi = None

        _add_error_schemas_to_openapi(mock_app)

        # Verify that app.openapi was set to a function
        assert callable(mock_app.openapi)

    def test_add_error_schemas_to_openapi_caches_schema(self):
        """Test that the enhanced OpenAPI generator caches the schema."""
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi_schema = {"existing": "schema"}
        mock_app.title = "Test API"
        mock_app.version = "1.0.0"
        mock_app.description = "Test Description"
        mock_app.routes = []

        _add_error_schemas_to_openapi(mock_app)

        # Call the generator
        result = mock_app.openapi()

        # Should return the cached schema
        assert result == {"existing": "schema"}

    def test_add_error_schemas_to_openapi_generates_new_schema(self):
        """
        Test that the enhanced OpenAPI generator creates new schema when none exists.
        """
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi_schema = None
        mock_app.title = "Test API"
        mock_app.version = "1.0.0"
        mock_app.description = "Test Description"
        mock_app.routes = []

        _add_error_schemas_to_openapi(mock_app)

        # Mock the import that happens inside the enhanced_openapi_generator
        with patch("fastapi.openapi.utils.get_openapi") as mock_get_openapi:
            mock_openapi_schema = {
                "paths": {
                    "/test": {"get": {"responses": {"200": {"description": "Success"}}}}
                }
            }
            mock_get_openapi.return_value = mock_openapi_schema

            with patch(
                "app.src.core.exceptions.exception_handlers."
                "_add_error_responses_to_endpoint"
            ) as mock_add_responses:
                mock_app.openapi()

                # Verify get_openapi was called
                mock_get_openapi.assert_called_once_with(
                    title="Test API",
                    version="1.0.0",
                    description="Test Description",
                    routes=[],
                )

                # Verify error responses were added
                mock_add_responses.assert_called_once()

                # Verify schema was cached
                assert mock_app.openapi_schema == mock_openapi_schema

    def test_add_error_responses_to_endpoint_adds_missing_responses(self):
        """Test that _add_error_responses_to_endpoint adds missing error responses."""
        responses = {"200": {"description": "Success"}}

        # Mock the import that happens inside _add_error_responses_to_endpoint
        with (
            patch(
                "app.src.core.exceptions.exception_schemas.ValidationErrorResponse"
            ) as mock_validation_response,
            patch(
                "app.src.core.exceptions.exception_schemas.ServerErrorResponse"
            ) as mock_server_response,
        ):
            mock_validation_response.model_json_schema.return_value = {
                "validation": "schema"
            }
            mock_server_response.model_json_schema.return_value = {"server": "schema"}

            _add_error_responses_to_endpoint(responses)

            # Verify 400 response was added
            assert "400" in responses
            assert responses["400"]["description"] == "Bad Request"
            assert responses["400"]["content"]["application/json"]["schema"] == {
                "validation": "schema"
            }

            # Verify 500 response was added
            assert "500" in responses
            assert responses["500"]["description"] == "Internal Server Error"
            assert responses["500"]["content"]["application/json"]["schema"] == {
                "server": "schema"
            }

    def test_add_error_responses_to_endpoint_preserves_existing_responses(self):
        """
        Test that _add_error_responses_to_endpoint preserves existing error responses.
        """
        responses = {
            "200": {"description": "Success"},
            "400": {"description": "Custom Bad Request"},
            "500": {"description": "Custom Server Error"},
        }
        original_responses = responses.copy()

        _add_error_responses_to_endpoint(responses)

        # Verify existing responses were not modified
        assert responses["400"] == original_responses["400"]
        assert responses["500"] == original_responses["500"]
        assert responses["200"] == original_responses["200"]

    def test_add_error_responses_to_endpoint_partial_existing_responses(self):
        """Test adding responses when only some error responses exist."""
        responses = {
            "200": {"description": "Success"},
            "400": {"description": "Existing Bad Request"},
        }

        with patch(
            "app.src.core.exceptions.exception_schemas.ServerErrorResponse"
        ) as mock_server_response:
            mock_server_response.model_json_schema.return_value = {"server": "schema"}

            _add_error_responses_to_endpoint(responses)

            # Verify 400 was not modified
            assert responses["400"]["description"] == "Existing Bad Request"

            # Verify 500 was added
            assert "500" in responses
            assert responses["500"]["description"] == "Internal Server Error"


class TestIntegrationScenarios:
    """Test integration scenarios for exception handlers."""

    @pytest.fixture
    def mock_app_with_handlers(self):
        """Create a mock FastAPI app with handlers set up."""
        app = Mock(spec=FastAPI)
        handlers = {}

        def exception_handler(exc_type):
            def decorator(handler_func):
                handlers[exc_type] = handler_func
                return handler_func

            return decorator

        app.exception_handler = exception_handler
        app.handlers = handlers  # Store for test access

        setup_exception_handlers(app)
        return app

    @pytest.mark.asyncio
    async def test_complete_api_exception_flow(self, mock_app_with_handlers):
        """Test complete flow for API exception handling."""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "PUT"

        exception = BaseAPIException(
            message="Validation failed", status_code=422, detail="Invalid input data"
        )

        handler = mock_app_with_handlers.handlers[BaseAPIException]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "integration-test-id"
            mock_create_response.return_value = {
                "error": "Validation failed",
                "detail": "Invalid input data",
            }

            result = await handler(mock_request, exception)

            # Verify complete flow
            assert isinstance(result, JSONResponse)
            assert result.status_code == 422

            # Verify logging
            mock_logger.warning.assert_called_once()
            log_call = mock_logger.warning.call_args
            assert "Validation failed" in log_call[0][0]
            assert log_call[1]["extra"]["request_id"] == "integration-test-id"
            assert log_call[1]["extra"]["method"] == "PUT"
            assert log_call[1]["extra"]["path"] == "/api/test"

    @pytest.mark.asyncio
    async def test_complete_general_exception_flow(self, mock_app_with_handlers):
        """Test complete flow for general exception handling."""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/crash"
        mock_request.method = "DELETE"

        exception = RuntimeError("Database connection failed")

        handler = mock_app_with_handlers.handlers[Exception]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers."
                "create_server_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = "crash-test-id"
            mock_create_response.return_value = {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            }

            result = await handler(mock_request, exception)

            # Verify complete flow
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500

            # Verify error logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args
            assert "Unhandled exception occurred" in log_call[0][0]
            assert log_call[1]["extra"]["request_id"] == "crash-test-id"
            assert log_call[1]["extra"]["exception_type"] == "RuntimeError"
            assert log_call[1]["exc_info"] is exception


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_handler_with_missing_request_id(self):
        """Test handler behavior when request_id is not available."""
        mock_app = Mock(spec=FastAPI)
        handler_registry = {}

        def register_handler(exc_type):
            def decorator(handler_func):
                handler_registry[exc_type] = handler_func
                return handler_func

            return decorator

        mock_app.exception_handler = register_handler
        setup_exception_handlers(mock_app)

        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"

        exception = BaseAPIException("Test error")

        handler = handler_registry[BaseAPIException]

        with (
            patch("app.src.core.exceptions.exception_handlers.logger") as mock_logger,
            patch(
                "app.src.core.exceptions.exception_handlers.get_request_id"
            ) as mock_get_request_id,
            patch(
                "app.src.core.exceptions.exception_handlers.create_api_error_response"
            ) as mock_create_response,
        ):
            mock_get_request_id.return_value = None  # No request ID available
            mock_create_response.return_value = {"error": "test"}

            result = await handler(mock_request, exception)

            # Verify it still works
            assert isinstance(result, JSONResponse)

            # Verify logging includes None request_id
            log_call = mock_logger.warning.call_args
            assert log_call[1]["extra"]["request_id"] is None

    def test_openapi_enhancement_with_empty_paths(self):
        """Test OpenAPI enhancement when no paths exist."""
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi_schema = None
        mock_app.title = "Test API"
        mock_app.version = "1.0.0"
        mock_app.description = "Test Description"
        mock_app.routes = []

        _add_error_schemas_to_openapi(mock_app)

        with patch("fastapi.openapi.utils.get_openapi") as mock_get_openapi:
            mock_get_openapi.return_value = {"paths": {}}

            # Should not raise any errors
            result = mock_app.openapi()
            assert "paths" in result

    def test_openapi_enhancement_with_malformed_paths(self):
        """Test OpenAPI enhancement with malformed path data."""
        mock_app = Mock(spec=FastAPI)
        mock_app.openapi_schema = None
        mock_app.title = "Test API"
        mock_app.version = "1.0.0"
        mock_app.description = "Test Description"
        mock_app.routes = []

        _add_error_schemas_to_openapi(mock_app)

        with patch("fastapi.openapi.utils.get_openapi") as mock_get_openapi:
            # Malformed paths - some entries are not dicts
            mock_get_openapi.return_value = {
                "paths": {
                    "/test1": {
                        "get": "not a dict",  # This should be skipped
                        "post": {"responses": {}},  # This should be processed
                    }
                }
            }

            with patch(
                "app.src.core.exceptions.exception_handlers."
                "_add_error_responses_to_endpoint"
            ) as mock_add_responses:
                mock_app.openapi()

                # Should only be called once for the valid method
                mock_add_responses.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
