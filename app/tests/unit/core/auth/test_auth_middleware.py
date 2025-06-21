from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from app.src.core.auth.api_key_service import APIKeyService
from app.src.core.auth.exceptions import AuthenticationRequiredError
from app.src.core.auth.middleware import (
    AUTH_HEADER_NAME,
    BEARER_PREFIX,
    DEFAULT_EXEMPT_PATHS,
    AuthenticationMiddleware,
)


class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware class."""

    def test_inherits_from_base_http_middleware(self):
        """Test that AuthenticationMiddleware inherits from BaseHTTPMiddleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        assert issubclass(AuthenticationMiddleware, BaseHTTPMiddleware)

    def test_constructor_with_default_exempt_paths(self):
        """Test middleware initialization with default exempt paths."""
        app = Mock(spec=ASGIApp)
        api_key_service = Mock(spec=APIKeyService)

        middleware = AuthenticationMiddleware(app, api_key_service)

        assert middleware.api_key_service is api_key_service
        assert middleware.exempt_paths == DEFAULT_EXEMPT_PATHS

    def test_constructor_with_custom_exempt_paths(self):
        """Test middleware initialization with custom exempt paths."""
        app = Mock(spec=ASGIApp)
        api_key_service = Mock(spec=APIKeyService)
        custom_paths = {"/custom/path", "/another/path"}

        middleware = AuthenticationMiddleware(app, api_key_service, custom_paths)

        assert middleware.api_key_service is api_key_service
        assert middleware.exempt_paths == custom_paths

    def test_constructor_with_none_exempt_paths_uses_default(self):
        """Test that passing None for exempt_paths uses default."""
        app = Mock(spec=ASGIApp)
        api_key_service = Mock(spec=APIKeyService)

        middleware = AuthenticationMiddleware(app, api_key_service, None)

        assert middleware.exempt_paths == DEFAULT_EXEMPT_PATHS


class TestIsExemptPath:
    """Test _is_exempt_path method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)

    def test_default_exempt_paths_are_exempt(self):
        """Test that default exempt paths return True."""
        middleware = AuthenticationMiddleware(self.app, self.api_key_service)

        for path in DEFAULT_EXEMPT_PATHS:
            assert middleware._is_exempt_path(path) is True

    def test_custom_exempt_paths_are_exempt(self):
        """Test that custom exempt paths return True."""
        custom_paths = {"/custom", "/special/endpoint"}
        middleware = AuthenticationMiddleware(
            self.app, self.api_key_service, custom_paths
        )

        for path in custom_paths:
            assert middleware._is_exempt_path(path) is True

    def test_non_exempt_paths_are_not_exempt(self):
        """Test that non-exempt paths return False."""
        middleware = AuthenticationMiddleware(self.app, self.api_key_service)

        non_exempt_paths = [
            "/api/v1/tasks",
            "/api/v1/vault/pull",
            "/admin",
            "/user/profile",
            "/api/v1/health/extended",  # Similar but not exact match
        ]

        for path in non_exempt_paths:
            assert middleware._is_exempt_path(path) is False

    def test_path_matching_is_exact(self):
        """Test that path matching is exact, not partial."""
        middleware = AuthenticationMiddleware(self.app, self.api_key_service)

        # These should NOT match /api/v1/health
        non_matching_paths = [
            "/api/v1/health/status",
            "/api/v1/healthcheck",
            "/api/v1/health/",
            "prefix/api/v1/health",
        ]

        for path in non_matching_paths:
            assert middleware._is_exempt_path(path) is False


class TestExtractAPIKey:
    """Test _extract_api_key method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)
        self.middleware = AuthenticationMiddleware(self.app, self.api_key_service)

    def test_extracts_valid_bearer_token(self):
        """Test successful extraction of valid Bearer token."""
        request = Mock(spec=Request)
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}valid-api-key-123"}

        result = self.middleware._extract_api_key(request)

        assert result == "valid-api-key-123"

    def test_extracts_bearer_token_with_extra_whitespace(self):
        """Test extraction with extra whitespace around token."""
        request = Mock(spec=Request)
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}  token-with-spaces  "}

        result = self.middleware._extract_api_key(request)

        assert result == "token-with-spaces"

    def test_raises_when_authorization_header_missing(self):
        """Test exception when Authorization header is missing."""
        request = Mock(spec=Request)
        request.headers = {}

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            self.middleware._extract_api_key(request)

        assert exc_info.value.message == "Missing Authorization header"
        assert exc_info.value.status_code == 401

    def test_raises_when_authorization_header_is_none(self):
        """Test exception when Authorization header is None."""
        request = Mock(spec=Request)
        request.headers = {AUTH_HEADER_NAME: None}

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            self.middleware._extract_api_key(request)

        assert exc_info.value.message == "Missing Authorization header"

    def test_raises_when_authorization_header_not_bearer(self):
        """Test exception when Authorization header doesn't start with Bearer."""
        invalid_headers = [
            "Basic dXNlcjpwYXNz",
            "Token abc123",
            "bearer token-lowercase",  # Case sensitive
            "Bearer",  # Missing space
            "APIKey my-key",
            "oauth2-token",
        ]

        for invalid_header in invalid_headers:
            request = Mock(spec=Request)
            request.headers = {AUTH_HEADER_NAME: invalid_header}

            with pytest.raises(AuthenticationRequiredError) as exc_info:
                self.middleware._extract_api_key(request)

            assert exc_info.value.message == "Invalid Authorization header format"

    def test_raises_when_api_key_is_empty_after_bearer(self):
        """Test exception when API key is empty after Bearer prefix."""
        empty_tokens = [
            f"{BEARER_PREFIX}",  # Just "Bearer "
            f"{BEARER_PREFIX}   ",  # Just whitespace
            f"{BEARER_PREFIX}\t\n",  # Just tabs/newlines
        ]

        for empty_token in empty_tokens:
            request = Mock(spec=Request)
            request.headers = {AUTH_HEADER_NAME: empty_token}

            with pytest.raises(AuthenticationRequiredError) as exc_info:
                self.middleware._extract_api_key(request)

            assert exc_info.value.message == "Empty API key"

    def test_handles_various_valid_api_key_formats(self):
        """Test extraction of various valid API key formats."""
        valid_keys = [
            "simple-key",
            "key_with_underscores",
            "key-with-numbers-123",
            "UPPERCASE-KEY",
            "MiXeD-CaSe-KeY",
            "very-long-api-key-with-multiple-segments-and-special-chars",
            "a",  # Single character
            "key.with.dots",
            "key+with+plus",
            "key=with=equals",
        ]

        for valid_key in valid_keys:
            request = Mock(spec=Request)
            request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}{valid_key}"}

            result = self.middleware._extract_api_key(request)

            assert result == valid_key


class TestDispatchMethod:
    """Test main dispatch method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)
        self.middleware = AuthenticationMiddleware(self.app, self.api_key_service)

    @pytest.mark.asyncio
    async def test_exempt_path_bypasses_authentication(self):
        """Test that exempt paths bypass authentication entirely."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/health"

        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        response = await self.middleware.dispatch(request, call_next)

        # Should call next without any authentication
        call_next.assert_called_once_with(request)
        assert response == call_next.return_value

        # Should not call API key service
        self.api_key_service.validate_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_authentication_flow(self):
        """Test complete successful authentication flow."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}valid-key"}
        request.state = Mock()

        # Mock successful key validation
        self.api_key_service.validate_key = AsyncMock(return_value=True)
        call_next = AsyncMock(return_value=JSONResponse({"data": "success"}))

        response = await self.middleware.dispatch(request, call_next)

        # Verify API key service was called
        self.api_key_service.validate_key.assert_called_once_with("valid-key")

        # Verify request state was set
        assert request.state.api_key == "valid-key"
        assert request.state.authenticated is True

        # Verify next was called and response returned
        call_next.assert_called_once_with(request)
        assert response == call_next.return_value

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_error_response(self):
        """Test that invalid API key returns proper error response."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}invalid-key"}
        request.client = Mock()
        request.client.host = "192.168.1.100"

        # Mock failed key validation
        self.api_key_service.validate_key = AsyncMock(return_value=False)
        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            response = await self.middleware.dispatch(request, call_next)

        # Verify API key service was called
        self.api_key_service.validate_key.assert_called_once_with("invalid-key")

        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401  # InvalidAPIKeyError status code

        # Verify logging
        mock_logger.warning.assert_called_once()
        log_call_args = mock_logger.warning.call_args[0][0]
        assert "192.168.1.100" in log_call_args
        assert "Invalid API key provided" in log_call_args

        # Verify next was NOT called
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_authorization_header_returns_error_response(self):
        """Test that missing Authorization header returns proper error response."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {}
        request.client = Mock()
        request.client.host = "10.0.0.1"

        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            response = await self.middleware.dispatch(request, call_next)

        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401  # AuthenticationRequiredError status code

        # Verify response content
        response_data = response.body.decode()
        assert "Missing Authorization header" in response_data

        # Verify logging
        mock_logger.warning.assert_called_once()
        log_call_args = mock_logger.warning.call_args[0][0]
        assert "10.0.0.1" in log_call_args
        assert "Missing Authorization header" in log_call_args

        # Verify next was NOT called
        call_next.assert_not_called()

        # Verify API key service was NOT called
        self.api_key_service.validate_key.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_authorization_format_returns_error_response(self):
        """Test that invalid Authorization format returns proper error response."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/vault/pull"
        request.headers = {AUTH_HEADER_NAME: "Basic dXNlcjpwYXNz"}
        request.client = Mock()
        request.client.host = "172.16.0.5"

        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            response = await self.middleware.dispatch(request, call_next)

        # Verify error response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        # Verify response content
        response_data = response.body.decode()
        assert "Invalid Authorization header format" in response_data

        # Verify logging includes client IP
        mock_logger.warning.assert_called_once()
        log_call_args = mock_logger.warning.call_args[0][0]
        assert "172.16.0.5" in log_call_args

    @pytest.mark.asyncio
    async def test_missing_client_ip_uses_unknown_in_logs(self):
        """Test that missing client IP uses 'unknown' in logs."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {}
        request.client = None  # No client info

        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            response = await self.middleware.dispatch(request, call_next)

        # Verify error response is returned
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        # Verify logging uses 'unknown' for IP
        mock_logger.warning.assert_called_once()
        log_call_args = mock_logger.warning.call_args[0][0]
        assert "unknown" in log_call_args
        assert "Authentication failed for unknown" in log_call_args

    @pytest.mark.asyncio
    async def test_api_key_service_exception_is_not_caught(self):
        """Test that unexpected APIKeyService exceptions are not caught."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}valid-key"}

        # Mock service to raise unexpected exception
        self.api_key_service.validate_key = AsyncMock(
            side_effect=ValueError("Service error")
        )
        call_next = AsyncMock()

        with pytest.raises(ValueError, match="Service error"):
            await self.middleware.dispatch(request, call_next)

    @pytest.mark.asyncio
    async def test_multiple_exempt_paths_work_correctly(self):
        """Test that all default exempt paths work correctly."""
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        for exempt_path in DEFAULT_EXEMPT_PATHS:
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = exempt_path

            response = await self.middleware.dispatch(request, call_next)

            # Should bypass authentication
            assert response == call_next.return_value

        # Verify call_next was called for each exempt path
        assert call_next.call_count == len(DEFAULT_EXEMPT_PATHS)

        # Verify API key service was never called
        self.api_key_service.validate_key.assert_not_called()


class TestErrorResponseFormat:
    """Test error response format and content."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)
        self.middleware = AuthenticationMiddleware(self.app, self.api_key_service)

    @pytest.mark.asyncio
    async def test_authentication_required_error_response_format(self):
        """Test the format of AuthenticationRequiredError responses."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        call_next = AsyncMock()

        response = await self.middleware.dispatch(request, call_next)

        # Verify response is JSONResponse
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        # Verify response content structure
        response_data = response.body.decode()
        assert '"error"' in response_data
        assert '"status_code"' in response_data
        assert '"Missing Authorization header"' in response_data
        assert "401" in response_data

    @pytest.mark.asyncio
    async def test_invalid_api_key_error_response_format(self):
        """Test the format of InvalidAPIKeyError responses."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}bad-key"}
        request.client = Mock()
        request.client.host = "10.0.0.1"

        self.api_key_service.validate_key = AsyncMock(return_value=False)
        call_next = AsyncMock()

        response = await self.middleware.dispatch(request, call_next)

        # Verify response format
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

        response_data = response.body.decode()
        assert '"error"' in response_data
        assert '"status_code"' in response_data
        assert '"Invalid API key provided"' in response_data
        assert "401" in response_data


class TestLoggingBehavior:
    """Test logging behavior in detail."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)
        self.middleware = AuthenticationMiddleware(self.app, self.api_key_service)

    @pytest.mark.asyncio
    async def test_logging_includes_client_ip_and_error_message(self):
        """Test that logging includes both client IP and error message."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: "Invalid format"}
        request.client = Mock()
        request.client.host = "203.0.113.1"

        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            await self.middleware.dispatch(request, call_next)

        # Verify logging call
        mock_logger.warning.assert_called_once()
        log_call = mock_logger.warning.call_args[0][0]

        # Verify log format: "Authentication failed for {client_ip}: {error_message}"
        assert log_call.startswith("Authentication failed for 203.0.113.1:")
        assert "Invalid Authorization header format" in log_call

    @pytest.mark.asyncio
    async def test_logging_level_is_warning(self):
        """Test that authentication failures are logged at WARNING level."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        call_next = AsyncMock()

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            await self.middleware.dispatch(request, call_next)

        # Verify WARNING level is used, not ERROR or INFO
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
        mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_authentication_does_not_log(self):
        """Test that successful authentication doesn't generate log entries."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}valid-key"}
        request.state = Mock()

        self.api_key_service.validate_key = AsyncMock(return_value=True)
        call_next = AsyncMock(return_value=JSONResponse({"success": True}))

        with patch("app.src.core.auth.middleware.logger") as mock_logger:
            await self.middleware.dispatch(request, call_next)

        # Verify no logging occurred
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.info.assert_not_called()


class TestIntegrationScenarios:
    """Test integration scenarios and realistic usage patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock(spec=ASGIApp)
        self.api_key_service = Mock(spec=APIKeyService)

    @pytest.mark.asyncio
    async def test_custom_exempt_paths_integration(self):
        """Test middleware with custom exempt paths in realistic scenario."""
        custom_exempt_paths = {"/api/v1/health", "/api/v1/metrics", "/admin/status"}
        middleware = AuthenticationMiddleware(
            self.app, self.api_key_service, custom_exempt_paths
        )

        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

        # Test exempt paths
        for exempt_path in custom_exempt_paths:
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = exempt_path

            response = await middleware.dispatch(request, call_next)
            assert response == call_next.return_value

        # Test non-exempt path still requires auth
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {}
        request.client = Mock()
        request.client.host = "10.0.0.1"

        response = await middleware.dispatch(request, call_next)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_realistic_api_request_flow(self):
        """Test realistic API request flow with valid authentication."""
        middleware = AuthenticationMiddleware(self.app, self.api_key_service)

        # Simulate realistic request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/v1/tasks"
        request.headers = {
            AUTH_HEADER_NAME: f"{BEARER_PREFIX}sk-1234567890abcdef",
            "User-Agent": "MyApp/1.0",
            "Content-Type": "application/json",
        }
        request.state = Mock()
        request.client = Mock()
        request.client.host = "203.0.113.42"

        # Mock successful validation
        self.api_key_service.validate_key = AsyncMock(return_value=True)

        # Mock realistic response
        call_next = AsyncMock(
            return_value=JSONResponse(
                {"tasks": [{"id": 1, "title": "Test task"}], "count": 1}
            )
        )

        response = await middleware.dispatch(request, call_next)

        # Verify complete flow
        self.api_key_service.validate_key.assert_called_once_with("sk-1234567890abcdef")
        assert request.state.api_key == "sk-1234567890abcdef"
        assert request.state.authenticated is True
        call_next.assert_called_once_with(request)
        assert response == call_next.return_value

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self):
        """Test that middleware handles concurrent requests correctly."""
        import asyncio

        middleware = AuthenticationMiddleware(self.app, self.api_key_service)

        # Create multiple concurrent requests
        async def make_request(api_key: str, path: str):
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = path
            request.headers = {AUTH_HEADER_NAME: f"{BEARER_PREFIX}{api_key}"}
            request.state = Mock()
            request.client = Mock()
            request.client.host = "192.168.1.100"

            call_next = AsyncMock(return_value=JSONResponse({"success": True}))
            return await middleware.dispatch(request, call_next)

        # Mock service that validates specific keys
        async def mock_validate(key):
            await asyncio.sleep(0.01)  # Simulate async work
            return key.startswith("valid-")

        self.api_key_service.validate_key = mock_validate

        # Run concurrent requests
        tasks = [
            make_request("valid-key-1", "/api/v1/tasks"),
            make_request("invalid-key", "/api/v1/vault/pull"),
            make_request("valid-key-2", "/api/v1/tasks"),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        assert len(responses) == 3

        # First and third should succeed (valid keys)
        assert isinstance(responses[0], JSONResponse)
        assert responses[0].status_code == 200
        assert isinstance(responses[2], JSONResponse)
        assert responses[2].status_code == 200

        # Second should fail (invalid key)
        assert isinstance(responses[1], JSONResponse)
        assert responses[1].status_code == 401


class TestConstantsAndDefaults:
    """Test module constants and default values."""

    def test_default_exempt_paths_contain_expected_endpoints(self):
        """Test that DEFAULT_EXEMPT_PATHS contains expected endpoints."""
        expected_paths = {"/api/v1/health", "/docs", "/redoc"}

        assert DEFAULT_EXEMPT_PATHS == expected_paths
        assert isinstance(DEFAULT_EXEMPT_PATHS, frozenset)

    def test_auth_constants_have_correct_values(self):
        """Test that authentication constants have correct values."""
        assert AUTH_HEADER_NAME == "Authorization"
        assert BEARER_PREFIX == "Bearer "

    def test_bearer_prefix_has_trailing_space(self):
        """Test that BEARER_PREFIX includes trailing space for proper parsing."""
        assert BEARER_PREFIX.endswith(" ")
        assert len(BEARER_PREFIX) == 7  # "Bearer "


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
