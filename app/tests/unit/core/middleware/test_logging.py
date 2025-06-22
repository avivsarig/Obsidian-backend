import asyncio
import logging
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, Request, Response
from starlette.datastructures import URL, QueryParams

from app.src.core.middleware.logging import (
    RequestLoggingMiddleware,
    setup_logging_middleware,
)


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create a RequestLoggingMiddleware instance."""
        return RequestLoggingMiddleware(app=Mock())

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock(spec=URL)
        request.url.path = "/api/v1/test"
        request.query_params = QueryParams("param=value")
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        response = Mock(spec=Response)
        response.status_code = 200
        return response

    @pytest.mark.asyncio
    async def test_logs_request_start_and_completion(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test that middleware logs both request start and completion."""
        call_next = AsyncMock(return_value=mock_response)

        with patch(
            "app.src.core.middleware.logging.get_request_id",
            return_value="test-request-id",
        ), caplog.at_level(logging.INFO):
            result = await middleware.dispatch(mock_request, call_next)

        assert result == mock_response
        assert len(caplog.records) == 2

        start_record = caplog.records[0]
        assert start_record.message == "Request started"
        assert start_record.request_id == "test-request-id"
        assert start_record.method == "GET"
        assert start_record.path == "/api/v1/test"
        assert start_record.query_params == "param=value"
        assert start_record.client_ip == "127.0.0.1"
        assert start_record.user_agent == "test-agent"

        completion_record = caplog.records[1]
        assert completion_record.message == "Request completed"
        assert completion_record.request_id == "test-request-id"
        assert completion_record.method == "GET"
        assert completion_record.path == "/api/v1/test"
        assert completion_record.status_code == 200
        assert completion_record.process_time.endswith("s")

    @pytest.mark.asyncio
    async def test_logs_processing_time_accurately(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test that processing time is calculated accurately."""

        async def slow_call_next(request):
            await asyncio.sleep(0.1)
            return mock_response

        with patch(
            "app.src.core.middleware.logging.get_request_id", return_value="test-id"
        ), caplog.at_level(logging.INFO):
            start_time = time.time()
            await middleware.dispatch(mock_request, slow_call_next)
            end_time = time.time()

        completion_record = caplog.records[1]
        logged_time = float(completion_record.process_time.rstrip("s"))
        actual_time = end_time - start_time

        assert abs(logged_time - actual_time) < 0.01

    @pytest.mark.asyncio
    async def test_handles_missing_client_info(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test middleware handles requests without client information."""
        mock_request.client = None
        call_next = AsyncMock(return_value=mock_response)

        with patch(
            "app.src.core.middleware.logging.get_request_id", return_value="test-id"
        ), caplog.at_level(logging.INFO):
            await middleware.dispatch(mock_request, call_next)

        start_record = caplog.records[0]
        assert start_record.client_ip is None

    @pytest.mark.asyncio
    async def test_handles_missing_user_agent(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test middleware handles requests without user-agent header."""
        mock_request.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch(
            "app.src.core.middleware.logging.get_request_id", return_value="test-id"
        ), caplog.at_level(logging.INFO):
            await middleware.dispatch(mock_request, call_next)

        start_record = caplog.records[0]
        assert start_record.user_agent is None

    @pytest.mark.asyncio
    async def test_handles_empty_query_params(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test middleware handles requests with no query parameters."""
        mock_request.query_params = QueryParams()
        call_next = AsyncMock(return_value=mock_response)

        with patch(
            "app.src.core.middleware.logging.get_request_id", return_value="test-id"
        ), caplog.at_level(logging.INFO):
            await middleware.dispatch(mock_request, call_next)

        start_record = caplog.records[0]
        assert start_record.query_params == ""

    @pytest.mark.asyncio
    async def test_logs_different_http_methods(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test middleware logs different HTTP methods correctly."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        call_next = AsyncMock(return_value=mock_response)

        for method in methods:
            mock_request.method = method
            caplog.clear()

            with patch(
                "app.src.core.middleware.logging.get_request_id", return_value="test-id"
            ), caplog.at_level(logging.INFO):
                await middleware.dispatch(mock_request, call_next)

            assert caplog.records[0].method == method
            assert caplog.records[1].method == method

    @pytest.mark.asyncio
    async def test_logs_different_status_codes(self, middleware, mock_request, caplog):
        """Test middleware logs different response status codes."""
        status_codes = [200, 201, 400, 404, 500]

        for status_code in status_codes:
            mock_response = Mock(spec=Response)
            mock_response.status_code = status_code
            call_next = AsyncMock(return_value=mock_response)
            caplog.clear()

            with patch(
                "app.src.core.middleware.logging.get_request_id", return_value="test-id"
            ), caplog.at_level(logging.INFO):
                await middleware.dispatch(mock_request, call_next)

            completion_record = caplog.records[1]
            assert completion_record.status_code == status_code

    @pytest.mark.asyncio
    async def test_propagates_exceptions_from_call_next(self, middleware, mock_request):
        """Test middleware propagates exceptions from downstream handlers."""
        test_exception = ValueError("Test error")
        call_next = AsyncMock(side_effect=test_exception)

        with patch(
            "app.src.core.middleware.logging.get_request_id", return_value="test-id"
        ), pytest.raises(ValueError, match="Test error"):
            await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_uses_request_tracking_for_request_id(
        self, middleware, mock_request, mock_response, caplog
    ):
        """Test middleware uses request tracking module for request ID."""
        call_next = AsyncMock(return_value=mock_response)

        with patch("app.src.core.middleware.logging.get_request_id") as mock_get_id:
            mock_get_id.return_value = "unique-request-id-123"

            with caplog.at_level(logging.INFO):
                await middleware.dispatch(mock_request, call_next)

        assert mock_get_id.call_count == 2
        assert caplog.records[0].request_id == "unique-request-id-123"
        assert caplog.records[1].request_id == "unique-request-id-123"


class TestSetupLoggingMiddleware:
    """Test setup_logging_middleware function."""

    def test_adds_middleware_to_app(self):
        """Test that setup function adds middleware to FastAPI app."""
        app = Mock(spec=FastAPI)

        setup_logging_middleware(app)

        app.add_middleware.assert_called_once_with(RequestLoggingMiddleware)

    def test_works_with_real_fastapi_app(self):
        """Test setup function works with actual FastAPI instance."""
        app = FastAPI()
        initial_middleware_count = len(app.user_middleware)

        setup_logging_middleware(app)

        assert len(app.user_middleware) == initial_middleware_count + 1
        middleware_cls = app.user_middleware[0].cls
        assert middleware_cls == RequestLoggingMiddleware
