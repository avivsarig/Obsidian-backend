from unittest.mock import Mock

import pytest
from fastapi import Request

from app.src.core.auth.exceptions import AuthenticationRequiredError
from app.src.core.auth.middleware import require_api_key


class TestRequireAPIKey:
    """Test require_api_key middleware function."""

    @pytest.mark.asyncio
    async def test_returns_api_key_when_authenticated_with_valid_key(self):
        """Test successful authentication with valid API key."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        request.state.api_key = "valid-api-key"

        result = await require_api_key(request)

        assert result == "valid-api-key"

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_not_authenticated(self):
        """Test exception when request is not authenticated."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = False
        request.state.api_key = "some-key"

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Request not authenticated"
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_authenticated_attribute_missing(
        self,
    ):
        """Test exception when authenticated attribute is missing from request state."""
        request = Mock(spec=Request)
        request.state = Mock()
        delattr(request.state, "authenticated") if hasattr(
            request.state, "authenticated"
        ) else None

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Request not authenticated"
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_api_key_is_none(self):
        """Test exception when API key is None."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        request.state.api_key = None

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Invalid API key in request state"
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_api_key_missing(self):
        """Test exception when API key attribute is missing from request state."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        delattr(request.state, "api_key") if hasattr(request.state, "api_key") else None

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Invalid API key in request state"
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_api_key_is_not_string(self):
        """Test exception when API key is not a string type."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        request.state.api_key = 12345  # Integer instead of string

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Invalid API key in request state"
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_authentication_required_when_api_key_is_empty_string(self):
        """Test exception when API key is empty string."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        request.state.api_key = ""

        result = await require_api_key(request)

        assert result == ""

    @pytest.mark.asyncio
    async def test_handles_different_valid_string_api_keys(self):
        """Test that various valid string API keys are returned correctly."""
        test_keys = [
            "simple-key",
            "key-with-numbers-123",
            "key_with_underscores",
            "KEY-WITH-CAPS",
            "very-long-api-key-with-multiple-segments-and-characters-123",
            "a",  # Single character
            "key with spaces",
        ]

        for test_key in test_keys:
            request = Mock(spec=Request)
            request.state = Mock()
            request.state.authenticated = True
            request.state.api_key = test_key

            result = await require_api_key(request)

            assert result == test_key

    @pytest.mark.asyncio
    async def test_authentication_attribute_falsy_values(self):
        """Test various falsy values for authentication attribute."""
        falsy_values = [False, None, 0, "", []]

        for falsy_value in falsy_values:
            request = Mock(spec=Request)
            request.state = Mock()
            request.state.authenticated = falsy_value
            request.state.api_key = "valid-key"

            with pytest.raises(AuthenticationRequiredError) as exc_info:
                await require_api_key(request)

            assert exc_info.value.message == "Request not authenticated"

    @pytest.mark.asyncio
    async def test_api_key_non_string_types(self):
        """Test various non-string types for API key."""
        non_string_values = [123, 45.67, [], {}, set(), object(), True]

        for non_string_value in non_string_values:
            request = Mock(spec=Request)
            request.state = Mock()
            request.state.authenticated = True
            request.state.api_key = non_string_value

            with pytest.raises(AuthenticationRequiredError) as exc_info:
                await require_api_key(request)

            assert exc_info.value.message == "Invalid API key in request state"


class TestRequestStateHandling:
    """Test edge cases in request state handling."""

    @pytest.mark.asyncio
    async def test_handles_missing_request_state(self):
        """Test behavior when request.state is missing."""
        request = Mock(spec=Request)
        delattr(request, "state")

        with pytest.raises(AttributeError):
            await require_api_key(request)

    @pytest.mark.asyncio
    async def test_handles_none_request_state(self):
        """Test behavior when request.state is None."""
        request = Mock(spec=Request)
        request.state = None

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert exc_info.value.message == "Request not authenticated"

    @pytest.mark.asyncio
    async def test_uses_getattr_default_behavior(self):
        """Test that getattr default behavior is used correctly."""

        # Create a simple object to test getattr behavior
        class SimpleState:
            pass

        request = Mock(spec=Request)
        request.state = SimpleState()

        # No authenticated attribute should default to False
        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert "Request not authenticated" in exc_info.value.message

        # Set authenticated but no api_key should default to None
        request.state.authenticated = True

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert "Invalid API key in request state" in exc_info.value.message


class TestMiddlewareIntegration:
    """Test integration scenarios with realistic request objects."""

    @pytest.mark.asyncio
    async def test_simulates_successful_auth_middleware_flow(self):
        """Test simulating a complete authentication middleware flow."""
        # Simulate what auth middleware would do
        request = Mock(spec=Request)
        request.state = Mock()

        # Step 1: Initially unauthenticated
        request.state.authenticated = False

        with pytest.raises(AuthenticationRequiredError):
            await require_api_key(request)

        # Step 2: After auth middleware processes valid key
        request.state.authenticated = True
        request.state.api_key = "authenticated-user-key"

        result = await require_api_key(request)
        assert result == "authenticated-user-key"

    @pytest.mark.asyncio
    async def test_simulates_failed_auth_middleware_flow(self):
        """Test simulating failed authentication middleware flow."""
        request = Mock(spec=Request)
        request.state = Mock()

        # Simulate auth middleware that failed to authenticate
        request.state.authenticated = False
        request.state.api_key = "invalid-key"  # Key present but not authenticated

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            await require_api_key(request)

        assert "Request not authenticated" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_multiple_sequential_calls_same_request(self):
        """Test calling require_api_key multiple times on the same request."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.authenticated = True
        request.state.api_key = "consistent-key"

        # Multiple calls should return the same result
        result1 = await require_api_key(request)
        result2 = await require_api_key(request)
        result3 = await require_api_key(request)

        assert result1 == result2 == result3 == "consistent-key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
