import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request, Response

from app.src.core.middleware.ip_rate_limiting import IPRateLimitMiddleware


class TestIPRateLimitMiddleware:
    """Test IP rate limiting middleware functionality."""

    def test_initialization_with_defaults(self):
        """Test middleware initialization with default parameters."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        assert middleware.requests_per_minute == 1000
        assert middleware.window_seconds == 60
        assert middleware.cleanup_interval == 300
        assert isinstance(middleware.requests, dict)
        assert isinstance(middleware.last_cleanup, float)

    def test_initialization_with_custom_params(self):
        """Test middleware initialization with custom parameters."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=100, window_seconds=30, cleanup_interval=150
        )

        assert middleware.requests_per_minute == 100
        assert middleware.window_seconds == 30
        assert middleware.cleanup_interval == 150

    @pytest.mark.asyncio
    async def test_allows_requests_within_limit(self):
        """Test that requests within rate limit are allowed through."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=5, window_seconds=60
        )

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Make 5 requests (within limit)
        for _ in range(5):
            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200
            assert call_next.call_count == _ + 1

    @pytest.mark.asyncio
    async def test_blocks_requests_exceeding_limit(self):
        """Test that requests exceeding rate limit return 429."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=3, window_seconds=60
        )

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Make 3 requests (at limit)
        for _ in range(3):
            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200

        # 4th request should be blocked
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429
        assert response.body == b"Rate limit exceeded"
        assert response.headers["Retry-After"] == "60"
        assert call_next.call_count == 3  # Should not have called next

    @pytest.mark.asyncio
    async def test_sliding_window_behavior(self):
        """Test that rate limit resets as sliding window moves."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, requests_per_minute=2, window_seconds=1)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Make 2 requests (at limit)
        for _ in range(2):
            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200

        # 3rd request should be blocked
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429

        # Wait for window to slide
        await asyncio.sleep(1.1)

        # Request should now be allowed
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tracks_multiple_ips_independently(self):
        """Test that different IPs are tracked independently."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=2, window_seconds=60
        )

        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "192.168.1.1"
        request1.headers = {}

        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "192.168.1.2"
        request2.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Exhaust limit for IP1
        for _ in range(2):
            response = await middleware.dispatch(request1, call_next)
            assert response.status_code == 200

        # IP1 should be blocked
        response = await middleware.dispatch(request1, call_next)
        assert response.status_code == 429

        # IP2 should still be allowed
        response = await middleware.dispatch(request2, call_next)
        assert response.status_code == 200


class TestIPExtraction:
    """Test IP address extraction functionality."""

    def test_extracts_direct_client_ip(self):
        """Test extraction of direct client IP."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.100"

    def test_extracts_forwarded_ip_single(self):
        """Test extraction of single forwarded IP."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "203.0.113.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_extracts_forwarded_ip_multiple(self):
        """Test extraction of first IP from multiple forwarded IPs."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1, 10.0.0.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_handles_forwarded_ip_with_whitespace(self):
        """Test extraction handles whitespace in forwarded header."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "  203.0.113.1  , 198.51.100.1"}

        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_fallback_to_unknown_when_no_client(self):
        """Test fallback to 'unknown' when no client info available."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = None
        request.headers = {}

        ip = middleware._get_client_ip(request)
        assert ip == "unknown"

    def test_fallback_to_unknown_when_no_host(self):
        """Test fallback to 'unknown' when client has no host."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = None
        request.headers = {}

        ip = middleware._get_client_ip(request)
        assert ip == "unknown"


class TestCleanupMechanism:
    """Test cleanup of old request entries."""

    def test_cleanup_removes_inactive_entries(self):
        """Test that cleanup removes entries for inactive IPs."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, cleanup_interval=0)  # Always cleanup

        # Add some old entries manually
        old_time = time.time() - 120  # 2 minutes ago
        middleware.requests["192.168.1.1"].append(old_time)
        middleware.requests["192.168.1.2"].append(old_time)
        middleware.requests["192.168.1.3"].append(time.time())  # Recent entry

        current_time = time.time()
        middleware._cleanup_old_entries(current_time)

        # Old entries should be removed, recent entry should remain
        assert "192.168.1.1" not in middleware.requests
        assert "192.168.1.2" not in middleware.requests
        assert "192.168.1.3" in middleware.requests

    def test_cleanup_respects_interval(self):
        """Test that cleanup only runs after interval has passed."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, cleanup_interval=60)

        # Add old entry
        old_time = time.time() - 120
        middleware.requests["192.168.1.1"].append(old_time)

        # Set last cleanup to recent time
        middleware.last_cleanup = time.time() - 30  # 30 seconds ago

        current_time = time.time()
        middleware._cleanup_old_entries(current_time)

        # Entry should still exist because interval hasn't passed
        assert "192.168.1.1" in middleware.requests

    def test_cleanup_updates_last_cleanup_time(self):
        """Test that cleanup updates the last cleanup timestamp."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, cleanup_interval=0)

        initial_cleanup_time = middleware.last_cleanup
        current_time = time.time()

        middleware._cleanup_old_entries(current_time)

        assert middleware.last_cleanup == current_time
        assert middleware.last_cleanup > initial_cleanup_time

    def test_cleanup_handles_empty_requests_dict(self):
        """Test that cleanup handles empty requests dictionary gracefully."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, cleanup_interval=0)

        # Ensure requests dict is empty
        middleware.requests.clear()

        current_time = time.time()
        # Should not raise any exception
        middleware._cleanup_old_entries(current_time)

        assert len(middleware.requests) == 0

    def test_cleanup_preserves_active_entries(self):
        """Test that cleanup preserves entries with recent requests."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, cleanup_interval=0)

        # Add mix of old and recent entries
        current_time = time.time()
        old_time = current_time - 120
        recent_time = current_time - 30

        middleware.requests["old_ip"].append(old_time)
        middleware.requests["mixed_ip"].append(old_time)
        middleware.requests["mixed_ip"].append(recent_time)
        middleware.requests["recent_ip"].append(recent_time)

        middleware._cleanup_old_entries(current_time)

        # Only old_ip should be removed
        assert "old_ip" not in middleware.requests
        assert "mixed_ip" in middleware.requests
        assert "recent_ip" in middleware.requests
        assert len(middleware.requests["mixed_ip"]) == 2  # Both entries preserved


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_handles_concurrent_requests_same_ip(self):
        """Test handling of concurrent requests from same IP."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=2, window_seconds=60
        )

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Simulate concurrent requests
        tasks = [middleware.dispatch(request, call_next) for _ in range(4)]

        responses = await asyncio.gather(*tasks)

        # Should have 2 successful (200) and 2 rate limited (429)
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)

        assert success_count == 2
        assert rate_limited_count == 2

    @pytest.mark.asyncio
    async def test_handles_zero_requests_per_minute(self):
        """Test behavior with zero requests per minute limit."""
        app = Mock()
        middleware = IPRateLimitMiddleware(
            app, requests_per_minute=0, window_seconds=60
        )

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # First request should be blocked immediately
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429
        assert call_next.call_count == 0

    @pytest.mark.asyncio
    async def test_handles_malformed_forwarded_header(self):
        """Test handling of malformed X-Forwarded-For header."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "not-an-ip"}

        ip = middleware._get_client_ip(request)
        # Should still extract the malformed value
        assert ip == "not-an-ip"

    @pytest.mark.asyncio
    async def test_handles_empty_forwarded_header(self):
        """Test handling of empty X-Forwarded-For header."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": ""}

        ip = middleware._get_client_ip(request)
        # Should fall back to client IP when forwarded header is empty
        assert ip == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_time_boundary_conditions(self):
        """Test behavior at time boundaries."""
        app = Mock()
        middleware = IPRateLimitMiddleware(app, requests_per_minute=1, window_seconds=1)

        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        call_next = AsyncMock(return_value=Response(content="success", status_code=200))

        # Make request at current time
        response1 = await middleware.dispatch(request, call_next)
        assert response1.status_code == 200

        # Second request should be blocked
        response2 = await middleware.dispatch(request, call_next)
        assert response2.status_code == 429

        # Wait for the window to slide, with more generous timing
        await asyncio.sleep(1.2)  # Increased buffer for timing precision

        # Request should now be allowed
        response3 = await middleware.dispatch(request, call_next)
        assert response3.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
