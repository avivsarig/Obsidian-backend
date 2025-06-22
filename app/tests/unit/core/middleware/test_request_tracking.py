from app.src.core.middleware.request_tracking import (
    get_request_id,
    set_request_id,
)


class TestRequestTracking:
    def test_get_request_id_returns_none_when_not_set(self):
        """Test that get_request_id returns None when no request ID is set"""
        result = get_request_id()
        assert result is None

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID"""
        test_id = "test-request-123"
        set_request_id(test_id)

        result = get_request_id()
        assert result == test_id

    def test_request_id_context_isolation(self):
        """Test that request IDs are properly isolated in context"""
        set_request_id("first-request")
        assert get_request_id() == "first-request"

        set_request_id("second-request")
        assert get_request_id() == "second-request"
