import logging
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.monitoring.alerts import send_alert_if_needed


class TestSendAlertIfNeeded:
    """Test the send_alert_if_needed function."""

    def create_mock_request(
        self, path: str = "/test", method: str = "GET"
    ) -> MagicMock:
        """Create a mock FastAPI Request object."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.method = method
        return mock_request

    def create_alertable_exception(
        self, should_alert: bool = True, status_code: int = 500
    ) -> BaseAPIException:
        """Create a BaseAPIException with alerting capability."""
        exc = BaseAPIException("Test exception", status_code=status_code)
        exc.should_alert = should_alert
        return exc

    @patch("app.src.core.monitoring.alerts.logger")
    def test_sends_alert_when_should_alert_true(self, mock_logger):
        """Test that alert is sent when exception has should_alert=True."""
        exc = self.create_alertable_exception(should_alert=True, status_code=500)
        request = self.create_mock_request("/api/test", "POST")
        request_id = "req-123"

        send_alert_if_needed(exc, request, request_id)

        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args

        assert call_args[0][0] == "Alert-worthy exception occurred"

        extra = call_args[1]["extra"]
        assert extra["request_id"] == "req-123"
        assert extra["exception_type"] == "BaseAPIException"
        assert extra["path"] == "/api/test"
        assert extra["method"] == "POST"
        assert extra["status_code"] == 500
        assert extra["alert"] is True

        assert call_args[1]["exc_info"] is exc

    @patch("app.src.core.monitoring.alerts.logger")
    def test_no_alert_when_should_alert_false(self, mock_logger):
        """Test that no alert is sent when exception has should_alert=False."""
        exc = self.create_alertable_exception(should_alert=False)
        request = self.create_mock_request()
        request_id = "req-123"

        send_alert_if_needed(exc, request, request_id)

        mock_logger.critical.assert_not_called()

    @patch("app.src.core.monitoring.alerts.logger")
    def test_no_alert_when_should_alert_missing(self, mock_logger):
        """Test that no alert is sent when exception lacks should_alert attribute."""
        exc = BaseAPIException("Test exception")
        request = self.create_mock_request()
        request_id = "req-123"

        send_alert_if_needed(exc, request, request_id)

        mock_logger.critical.assert_not_called()

    @patch("app.src.core.monitoring.alerts.logger")
    def test_handles_none_request_id(self, mock_logger):
        """Test that function handles None request_id gracefully."""
        exc = self.create_alertable_exception(should_alert=True)
        request = self.create_mock_request()

        send_alert_if_needed(exc, request, None)

        mock_logger.critical.assert_called_once()
        extra = mock_logger.critical.call_args[1]["extra"]
        assert extra["request_id"] is None

    @patch("app.src.core.monitoring.alerts.logger")
    def test_extracts_correct_request_metadata(self, mock_logger):
        """Test that request metadata is correctly extracted."""
        exc = self.create_alertable_exception(should_alert=True)
        request = self.create_mock_request("/api/v1/complex/path", "DELETE")

        send_alert_if_needed(exc, request, "test-id")

        extra = mock_logger.critical.call_args[1]["extra"]
        assert extra["path"] == "/api/v1/complex/path"
        assert extra["method"] == "DELETE"

    @patch("app.src.core.monitoring.alerts.logger")
    def test_includes_exception_status_code(self, mock_logger):
        """Test that exception status code is included in alert."""
        exc = self.create_alertable_exception(should_alert=True, status_code=503)
        request = self.create_mock_request()

        send_alert_if_needed(exc, request, "test-id")

        extra = mock_logger.critical.call_args[1]["extra"]
        assert extra["status_code"] == 503

    @patch("app.src.core.monitoring.alerts.logger")
    def test_includes_exception_type_name(self, mock_logger):
        """Test that exception type name is correctly captured."""

        class CustomException(BaseAPIException):
            pass

        exc = CustomException("Custom error")
        exc.should_alert = True
        request = self.create_mock_request()

        send_alert_if_needed(exc, request, "test-id")

        extra = mock_logger.critical.call_args[1]["extra"]
        assert extra["exception_type"] == "CustomException"


class TestAlertingIntegration:
    """Integration tests for the alerting system."""

    def test_function_signature_matches_expected_usage(self):
        """Test that function signature is compatible with expected usage patterns."""
        exc = BaseAPIException("Test")
        exc.should_alert = True
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"

        with patch("app.src.core.monitoring.alerts.logger"):
            send_alert_if_needed(exc, request, "test-123")
            send_alert_if_needed(exc, request, None)

    def test_works_with_real_logging_configuration(self):
        """Test that function works with actual logging setup."""
        logger = logging.getLogger("app.src.core.monitoring.alerts")

        with patch.object(logger, "critical") as mock_critical:
            exc = BaseAPIException("Real test")
            exc.should_alert = True
            request = MagicMock(spec=Request)
            request.url.path = "/real/test"
            request.method = "GET"

            send_alert_if_needed(exc, request, "real-test-id")

            mock_critical.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
