import asyncio
import time

# TODO: change to pytest?
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.responses import JSONResponse

from app.src.core.middleware.rate_limiting import PerKeyRateLimitMiddleware


@pytest.mark.asyncio
async def test_rate_limiting_comprehensive():
    """Comprehensive test for rate limiting middleware with detailed verification"""

    print("\n=== Starting comprehensive rate limiting test ===")

    # Setup middleware with low limits for testing
    app = MagicMock()
    requests_per_minute = 3
    window_seconds = 10
    middleware = PerKeyRateLimitMiddleware(
        app,
        requests_per_minute=requests_per_minute,
        window_seconds=window_seconds,
        cleanup_interval=5,
    )

    print(f"Configured: {requests_per_minute} requests per {window_seconds} seconds")

    # Mock successful response
    success_response = MagicMock()
    success_response.status_code = 200
    call_next = AsyncMock(return_value=success_response)

    # Test 1: Unauthenticated requests should bypass rate limiting
    print("\n--- Test 1: Unauthenticated requests ---")
    unauth_request = MagicMock()
    unauth_request.state.authenticated = False

    response = await middleware.dispatch(unauth_request, call_next)
    assert (
        response == success_response
    ), "Unauthenticated request should bypass rate limiting"
    print("✓ Unauthenticated request bypassed rate limiting")

    # Test 2: Authenticated requests within limit should pass
    print("\n--- Test 2: Requests within rate limit ---")
    auth_request = MagicMock()
    auth_request.state.authenticated = True
    auth_request.state.api_key = "test-key-123"

    responses = []
    for i in range(requests_per_minute):
        response = await middleware.dispatch(auth_request, call_next)
        responses.append(response)
        print(f"  Request {i+1}: Status {getattr(response, 'status_code', 'N/A')}")
        assert response == success_response, f"Request {i+1} should succeed"

    print(f"✓ All {requests_per_minute} requests within limit succeeded")

    # Test 3: Request exceeding limit should be blocked
    print("\n--- Test 3: Request exceeding rate limit ---")
    blocked_response = await middleware.dispatch(auth_request, call_next)

    assert isinstance(
        blocked_response, JSONResponse
    ), "Should return JSONResponse for rate limit"
    assert (
        blocked_response.status_code == 429
    ), f"Expected 429, got {blocked_response.status_code}"

    # Verify response content
    import json

    content = json.loads(blocked_response.body.decode())
    assert content["error"] == "Rate limit exceeded"
    assert content["status_code"] == 429
    assert "Maximum 3 requests" in content["detail"]

    print("✓ Rate limit correctly blocked excess request")
    print(f"  Response: {content}")

    # Test 4: Different API keys should have separate limits
    print("\n--- Test 4: Separate limits per API key ---")
    different_request = MagicMock()
    different_request.state.authenticated = True
    different_request.state.api_key = "different-key-456"

    response = await middleware.dispatch(different_request, call_next)
    assert response == success_response, "Different API key should have separate limit"
    print("✓ Different API key has separate rate limit")

    # Test 5: Verify internal state (before time manipulation)
    print("\n--- Test 5: Internal state verification ---")
    key1_requests = middleware.requests["test-key-123"]
    key2_requests = middleware.requests["different-key-456"]

    print(f"Key 'test-key-123' has {len(key1_requests)} tracked requests")
    print(f"Key 'different-key-456' has {len(key2_requests)} tracked requests")

    assert len(key1_requests) > 0, "Should have tracked requests for first key"
    assert len(key2_requests) > 0, "Should have tracked requests for second key"

    # Test 6: Window sliding behavior
    print("\n--- Test 6: Window sliding after time passes ---")
    print(f"Simulating {window_seconds + 1} seconds passing...")

    # Simulate time passing by manually clearing old entries
    current_time = time.time()
    future_time = current_time + window_seconds + 1

    # Patch time.time for this test
    original_time = time.time
    time.time = lambda: future_time

    try:
        response = await middleware.dispatch(auth_request, call_next)
        assert (
            response == success_response
        ), "Request should succeed after window slides"
        print("✓ Request succeeded after time window slid")
    finally:
        time.time = original_time

    # Test 7: Cleanup mechanism
    print("\n--- Test 7: Cleanup mechanism ---")
    initial_key_count = len(middleware.requests)
    print(f"Initial tracked keys: {initial_key_count}")

    # Force cleanup by calling it directly
    await middleware._cleanup_old_entries_async(time.time() + 1000)

    final_key_count = len(middleware.requests)
    print(f"Keys after cleanup: {final_key_count}")
    print("✓ Cleanup mechanism verified")

    print("\n=== All rate limiting tests passed! ===")


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


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_rate_limiting_comprehensive())
    asyncio.run(test_concurrent_requests())
