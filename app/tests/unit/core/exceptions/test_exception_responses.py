from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.exception_responses import (
    create_api_error_response,
    create_server_error_response,
)


class TestCreateAPIErrorResponse:
    """Test create_api_error_response function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        return request

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_basic_api_error_response(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test basic API error response structure."""
        mock_get_request_id.return_value = "test-request-id"
        mock_settings.environment = "production"

        exception = BaseAPIException("Test error", status_code=400)
        response = create_api_error_response(exception, mock_request)

        expected = {
            "error": "Test error",
            "status_code": 400,
            "request_id": "test-request-id",
        }

        assert response == expected
        mock_send_alert.assert_called_once_with(
            exception, mock_request, "test-request-id"
        )

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_with_detail(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response includes detail when provided."""
        mock_get_request_id.return_value = "test-request-id"
        mock_settings.environment = "production"

        exception = BaseAPIException(
            "Validation failed", status_code=422, detail="Field 'email' is required"
        )
        response = create_api_error_response(exception, mock_request)

        expected = {
            "error": "Validation failed",
            "status_code": 422,
            "request_id": "test-request-id",
            "detail": "Field 'email' is required",
        }

        assert response == expected

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_without_detail(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response excludes detail when None."""
        mock_get_request_id.return_value = "test-request-id"
        mock_settings.environment = "production"

        exception = BaseAPIException("Simple error", detail=None)
        response = create_api_error_response(exception, mock_request)

        assert "detail" not in response
        assert response["error"] == "Simple error"

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_development_mode(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response includes debug info in development."""
        mock_get_request_id.return_value = "dev-request-id"
        mock_settings.environment = "development"

        exception = BaseAPIException("Development error", status_code=404)
        response = create_api_error_response(exception, mock_request)

        assert response["error"] == "Development error"
        assert response["path"] == "/api/test"
        assert response["method"] == "GET"

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_production_mode(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response excludes debug info in production."""
        mock_get_request_id.return_value = "prod-request-id"
        mock_settings.environment = "production"

        exception = BaseAPIException("Production error")
        response = create_api_error_response(exception, mock_request)

        assert "path" not in response
        assert "method" not in response
        assert "original_error" not in response

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_with_original_error_development(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response includes original error in development."""
        mock_get_request_id.return_value = "dev-request-id"
        mock_settings.environment = "development"

        original_error = ValueError("Invalid value")
        exception = BaseAPIException("Wrapper error", original_error=original_error)
        response = create_api_error_response(exception, mock_request)

        assert "original_error" in response
        assert response["original_error"]["type"] == "ValueError"
        assert response["original_error"]["message"] == "Invalid value"

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_without_original_error_development(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response excludes original error when None."""
        mock_get_request_id.return_value = "dev-request-id"
        mock_settings.environment = "development"

        exception = BaseAPIException("No original error")
        response = create_api_error_response(exception, mock_request)

        assert "original_error" not in response

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_with_original_error_production(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response excludes original error in production."""
        mock_get_request_id.return_value = "prod-request-id"
        mock_settings.environment = "production"

        original_error = RuntimeError("Secret error")
        exception = BaseAPIException("Public error", original_error=original_error)
        response = create_api_error_response(exception, mock_request)

        assert "original_error" not in response

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_alert_called(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test that send_alert_if_needed is called with correct parameters."""
        mock_get_request_id.return_value = "alert-test-id"
        mock_settings.environment = "production"

        exception = BaseAPIException("Alert test error")
        create_api_error_response(exception, mock_request)

        mock_send_alert.assert_called_once_with(
            exception, mock_request, "alert-test-id"
        )

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_none_request_id(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response handles None request ID."""
        mock_get_request_id.return_value = None
        mock_settings.environment = "production"

        exception = BaseAPIException("No request ID error")
        response = create_api_error_response(exception, mock_request)

        assert response["request_id"] is None
        mock_send_alert.assert_called_once_with(exception, mock_request, None)

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_different_status_codes(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response with various status codes."""
        mock_get_request_id.return_value = "status-test-id"
        mock_settings.environment = "production"

        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (422, "Unprocessable Entity"),
            (500, "Internal Server Error"),
        ]

        for status_code, message in test_cases:
            exception = BaseAPIException(message, status_code=status_code)
            response = create_api_error_response(exception, mock_request)

            assert response["status_code"] == status_code
            assert response["error"] == message

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_api_error_response_complex_url_path(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test API error response with complex URL path."""
        mock_get_request_id.return_value = "complex-path-id"
        mock_settings.environment = "development"

        mock_request.url.path = "/api/v1/users/123/posts/456"
        mock_request.method = "DELETE"

        exception = BaseAPIException("Complex path error")
        response = create_api_error_response(exception, mock_request)

        assert response["path"] == "/api/v1/users/123/posts/456"
        assert response["method"] == "DELETE"


class TestCreateServerErrorResponse:
    """Test create_server_error_response function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/api/server"
        request.method = "POST"
        return request

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_basic_server_error_response(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test basic server error response structure."""
        mock_get_request_id.return_value = "server-error-id"
        mock_settings.environment = "production"

        exception = RuntimeError("Database connection failed")
        response = create_server_error_response(exception, mock_request)

        expected = {
            "error": "Internal server error",
            "status_code": 500,
            "request_id": "server-error-id",
            "detail": "An unexpected error occurred. Please try again.",
        }

        assert response == expected

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_development_mode(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response includes debug info in development."""
        mock_get_request_id.return_value = "dev-server-id"
        mock_settings.environment = "development"

        exception = ValueError("Invalid configuration")
        response = create_server_error_response(exception, mock_request)

        assert response["error"] == "Internal server error"
        assert response["status_code"] == 500
        assert response["path"] == "/api/server"
        assert response["method"] == "POST"
        assert response["exception_type"] == "ValueError"
        assert response["exception_message"] == "Invalid configuration"

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_production_mode(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response excludes debug info in production."""
        mock_get_request_id.return_value = "prod-server-id"
        mock_settings.environment = "production"

        exception = ConnectionError("Secret database details")
        response = create_server_error_response(exception, mock_request)

        assert "path" not in response
        assert "method" not in response
        assert "exception_type" not in response
        assert "exception_message" not in response

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_different_exception_types(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response with various exception types."""
        mock_get_request_id.return_value = "exception-type-id"
        mock_settings.environment = "development"

        exception_types = [
            ValueError("Invalid value"),
            TypeError("Wrong type"),
            RuntimeError("Runtime issue"),
            ConnectionError("Connection failed"),
            KeyError("Missing key"),
            AttributeError("Missing attribute"),
        ]

        for exception in exception_types:
            response = create_server_error_response(exception, mock_request)

            assert response["exception_type"] == type(exception).__name__
            assert response["exception_message"] == str(exception)
            assert response["status_code"] == 500

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_none_request_id(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response handles None request ID."""
        mock_get_request_id.return_value = None
        mock_settings.environment = "production"

        exception = Exception("Generic exception")
        response = create_server_error_response(exception, mock_request)

        assert response["request_id"] is None

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_empty_exception_message(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response with empty exception message."""
        mock_get_request_id.return_value = "empty-msg-id"
        mock_settings.environment = "development"

        exception = RuntimeError("")
        response = create_server_error_response(exception, mock_request)

        assert response["exception_type"] == "RuntimeError"
        assert response["exception_message"] == ""

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_custom_exception(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test server error response with custom exception class."""
        mock_get_request_id.return_value = "custom-exception-id"
        mock_settings.environment = "development"

        class CustomDatabaseError(Exception):
            pass

        exception = CustomDatabaseError("Custom database failure")
        response = create_server_error_response(exception, mock_request)

        assert response["exception_type"] == "CustomDatabaseError"
        assert response["exception_message"] == "Custom database failure"

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_server_error_response_fixed_fields(
        self, mock_settings, mock_get_request_id, mock_request
    ):
        """Test that server error response has fixed error message and status."""
        mock_get_request_id.return_value = "fixed-fields-id"
        mock_settings.environment = "production"

        # Test with different exceptions
        exceptions = [
            ValueError("Different message"),
            RuntimeError("Another message"),
            Exception("Generic message"),
        ]

        for exception in exceptions:
            response = create_server_error_response(exception, mock_request)

            # These should always be the same regardless of the exception
            assert response["error"] == "Internal server error"
            assert response["status_code"] == 500
            assert (
                response["detail"] == "An unexpected error occurred. Please try again."
            )


class TestResponseIntegration:
    """Test integration scenarios between both response functions."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.url.path = "/api/integration"
        request.method = "PUT"
        return request

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_response_format_consistency(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test that both functions produce consistent response formats."""
        mock_get_request_id.return_value = "consistency-test-id"
        mock_settings.environment = "production"

        # API error response
        api_exception = BaseAPIException("API error", status_code=400)
        api_response = create_api_error_response(api_exception, mock_request)

        # Server error response
        server_exception = RuntimeError("Server error")
        server_response = create_server_error_response(server_exception, mock_request)

        # Both should have these common fields
        common_fields = ["error", "status_code", "request_id"]
        for field in common_fields:
            assert field in api_response
            assert field in server_response

        # Both should have the same request_id
        assert api_response["request_id"] == server_response["request_id"]

    @patch("app.src.core.exceptions.exception_responses.get_request_id")
    @patch("app.src.core.exceptions.exception_responses.send_alert_if_needed")
    @patch("app.src.core.exceptions.exception_responses.settings")
    def test_development_debug_info_consistency(
        self, mock_settings, mock_send_alert, mock_get_request_id, mock_request
    ):
        """Test that both functions include similar debug info in development."""
        mock_get_request_id.return_value = "debug-consistency-id"
        mock_settings.environment = "development"

        # API error response
        api_exception = BaseAPIException("API debug error")
        api_response = create_api_error_response(api_exception, mock_request)

        # Server error response
        server_exception = ValueError("Server debug error")
        server_response = create_server_error_response(server_exception, mock_request)

        # Both should include path and method in development
        development_fields = ["path", "method"]
        for field in development_fields:
            assert field in api_response
            assert field in server_response
            assert api_response[field] == server_response[field]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
