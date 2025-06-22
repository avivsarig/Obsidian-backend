import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.responses import JSONResponse

from app.src.core.middleware.rate_limiting import PerKeyRateLimitMiddleware


@pytest.mark.asyncio
async def test_rate_limiting_comprehensive():
    app = MagicMock()
    requests_per_minute = 3
    window_seconds = 10
    middleware = PerKeyRateLimitMiddleware(
        app,
        requests_per_minute=requests_per_minute,
        window_seconds=window_seconds,
        cleanup_interval=5,
    )

    success_response = MagicMock()
    success_response.status_code = 200
    call_next = AsyncMock(return_value=success_response)

    unauth_request = MagicMock()
    unauth_request.state.authenticated = False

    response = await middleware.dispatch(unauth_request, call_next)
    assert response == success_response

    auth_request = MagicMock()
    auth_request.state.authenticated = True
    auth_request.state.api_key = "test-key-123"

    for _ in range(requests_per_minute):
        response = await middleware.dispatch(auth_request, call_next)
        assert response == success_response

    blocked_response = await middleware.dispatch(auth_request, call_next)

    assert isinstance(blocked_response, JSONResponse)
    assert blocked_response.status_code == 429

    import json

    content = json.loads(blocked_response.body.decode())
    assert content["error"] == "Rate limit exceeded"
    assert content["status_code"] == 429
    assert "Maximum 3 requests" in content["detail"]

    different_request = MagicMock()
    different_request.state.authenticated = True
    different_request.state.api_key = "different-key-456"

    response = await middleware.dispatch(different_request, call_next)
    assert response == success_response

    key1_requests = middleware.requests["test-key-123"]
    key2_requests = middleware.requests["different-key-456"]

    assert len(key1_requests) > 0
    assert len(key2_requests) > 0

    current_time = time.time()
    future_time = current_time + window_seconds + 1

    original_time = time.time
    time.time = lambda: future_time

    try:
        response = await middleware.dispatch(auth_request, call_next)
        assert response == success_response
    finally:
        time.time = original_time

    initial_key_count = len(middleware.requests)

    await middleware._cleanup_old_entries_async(time.time() + 1000)

    final_key_count = len(middleware.requests)
    assert final_key_count <= initial_key_count


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test rate limiting under concurrent load"""

    print("\n=== Testing concurrent requests ===")

    middleware = PerKeyRateLimitMiddleware(
        MagicMock(), requests_per_minute=5, window_seconds=60
    )

    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    # Create multiple concurrent requests
    requests = []
    for _i in range(10):
        request = MagicMock()
        request.state.authenticated = True
        request.state.api_key = "concurrent-test-key"
        requests.append(request)

    # Execute all requests concurrently
    tasks = [middleware.dispatch(req, call_next) for req in requests]
    responses = await asyncio.gather(*tasks)

    # Count successful vs rate-limited responses
    successful = sum(1 for r in responses if getattr(r, "status_code", 200) == 200)
    rate_limited = sum(1 for r in responses if getattr(r, "status_code", 200) == 429)

    print(f"Concurrent requests: {len(requests)}")
    print(f"Successful: {successful}")
    print(f"Rate limited: {rate_limited}")

    assert successful == 5, f"Expected 5 successful requests, got {successful}"
    assert rate_limited == 5, f"Expected 5 rate limited requests, got {rate_limited}"

    print("✓ Concurrent request handling verified")


@pytest.mark.asyncio
async def test_missing_api_key():
    """Test requests without API key bypass rate limiting"""
    middleware = PerKeyRateLimitMiddleware(MagicMock(), requests_per_minute=1)
    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    # Request without api_key attribute
    request_no_key = MagicMock()
    del request_no_key.state.api_key

    response = await middleware.dispatch(request_no_key, call_next)
    assert response.status_code == 200

    # Request with empty api_key
    request_empty_key = MagicMock()
    request_empty_key.state.api_key = ""
    request_empty_key.state.authenticated = True

    response = await middleware.dispatch(request_empty_key, call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_retry_after_header():
    """Test that 429 responses include proper Retry-After header"""
    window_seconds = 30
    middleware = PerKeyRateLimitMiddleware(
        MagicMock(), requests_per_minute=1, window_seconds=window_seconds
    )
    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    request = MagicMock()
    request.state.authenticated = True
    request.state.api_key = "test-key"

    # First request succeeds
    await middleware.dispatch(request, call_next)

    # Second request gets rate limited
    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert response.headers["Retry-After"] == str(window_seconds)


@pytest.mark.asyncio
async def test_cleanup_interval_respected():
    """Test that cleanup only runs after cleanup_interval seconds"""
    cleanup_interval = 100
    middleware = PerKeyRateLimitMiddleware(
        MagicMock(), requests_per_minute=1, cleanup_interval=cleanup_interval
    )

    # Initial cleanup time
    initial_cleanup = middleware.last_cleanup

    # Call cleanup with time just before interval
    await middleware._cleanup_old_entries_async(initial_cleanup + cleanup_interval - 1)
    assert middleware.last_cleanup == initial_cleanup

    # Call cleanup with time after interval
    await middleware._cleanup_old_entries_async(initial_cleanup + cleanup_interval + 1)
    assert middleware.last_cleanup > initial_cleanup


@pytest.mark.asyncio
async def test_sliding_window_cleanup_during_dispatch():
    """Test that old requests are cleaned up during normal dispatch flow"""
    middleware = PerKeyRateLimitMiddleware(
        MagicMock(), requests_per_minute=5, window_seconds=2
    )
    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    request = MagicMock()
    request.state.authenticated = True
    request.state.api_key = "test-key"

    # Make initial request
    await middleware.dispatch(request, call_next)

    # Simulate time passing beyond window
    import time

    original_time = time.time
    current_time = time.time()
    time.time = lambda: current_time + 3  # 3 seconds > 2 second window

    try:
        # This should trigger the popleft() cleanup in dispatch
        await middleware.dispatch(request, call_next)
        # Should succeed since old request was cleaned up
        assert len(middleware.requests["test-key"]) == 1
    finally:
        time.time = original_time


@pytest.mark.asyncio
async def test_custom_configuration():
    """Test middleware with custom configuration values"""
    custom_requests = 50
    custom_window = 120
    custom_cleanup = 600

    middleware = PerKeyRateLimitMiddleware(
        MagicMock(),
        requests_per_minute=custom_requests,
        window_seconds=custom_window,
        cleanup_interval=custom_cleanup,
    )

    assert middleware.requests_per_minute == custom_requests
    assert middleware.window_seconds == custom_window
    assert middleware.cleanup_interval == custom_cleanup


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_rate_limiting_comprehensive())
    asyncio.run(test_concurrent_requests())
    asyncio.run(test_missing_api_key())
    asyncio.run(test_retry_after_header())
    asyncio.run(test_cleanup_interval_respected())
    asyncio.run(test_custom_configuration())
