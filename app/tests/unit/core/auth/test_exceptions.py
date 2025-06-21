import pytest

from app.src.core.auth.exceptions import (
    AuthenticationRequiredError,
    InvalidAPIKeyError,
)
from app.src.core.exceptions.base_exceptions import BaseAPIException


class TestAuthenticationRequiredError:
    """Test AuthenticationRequiredError behavior and attributes."""

    def test_inherits_from_base_api_exception(self):
        error = AuthenticationRequiredError()

        assert isinstance(error, BaseAPIException)
        assert isinstance(error, Exception)

    def test_default_initialization(self):
        error = AuthenticationRequiredError()

        assert error.message == "Authentication required"
        assert error.status_code == 401
        assert error.detail == "Provide valid API key in Authorization header"
        assert error.should_alert is False
        assert str(error) == "Authentication required"

    def test_custom_message_initialization(self):
        custom_message = "You must authenticate to access this resource"
        error = AuthenticationRequiredError(message=custom_message)

        assert error.message == custom_message
        assert error.status_code == 401
        assert error.detail == "Provide valid API key in Authorization header"
        assert str(error) == custom_message

    def test_maintains_consistent_status_code(self):
        default_error = AuthenticationRequiredError()
        custom_error = AuthenticationRequiredError(message="Custom message")

        assert default_error.status_code == 401
        assert custom_error.status_code == 401

    def test_maintains_consistent_detail(self):
        default_error = AuthenticationRequiredError()
        custom_error = AuthenticationRequiredError(message="Custom message")

        expected_detail = "Provide valid API key in Authorization header"
        assert default_error.detail == expected_detail
        assert custom_error.detail == expected_detail

    def test_exception_can_be_raised_and_caught(self):
        with pytest.raises(AuthenticationRequiredError) as exc_info:
            raise AuthenticationRequiredError()

        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value)

    def test_exception_chain_preserved(self):
        original_error = ValueError("Original error")

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise AuthenticationRequiredError() from e

        assert exc_info.value.__cause__ is original_error


class TestInvalidAPIKeyError:
    """Test InvalidAPIKeyError behavior and attributes."""

    def test_inherits_from_base_api_exception(self):
        error = InvalidAPIKeyError()

        assert isinstance(error, BaseAPIException)
        assert isinstance(error, Exception)

    def test_default_initialization(self):
        error = InvalidAPIKeyError()

        assert error.message == "Invalid API key"
        assert error.status_code == 401
        assert error.detail == "The provided API key is not valid"
        assert error.should_alert is False
        assert str(error) == "Invalid API key"

    def test_custom_message_initialization(self):
        custom_message = "The API key you provided is expired"
        error = InvalidAPIKeyError(message=custom_message)

        assert error.message == custom_message
        assert error.status_code == 401
        assert error.detail == "The provided API key is not valid"
        assert str(error) == custom_message

    def test_maintains_consistent_status_code(self):
        default_error = InvalidAPIKeyError()
        custom_error = InvalidAPIKeyError(message="Custom message")

        assert default_error.status_code == 401
        assert custom_error.status_code == 401

    def test_maintains_consistent_detail(self):
        default_error = InvalidAPIKeyError()
        custom_error = InvalidAPIKeyError(message="Custom message")

        expected_detail = "The provided API key is not valid"
        assert default_error.detail == expected_detail
        assert custom_error.detail == expected_detail

    def test_exception_can_be_raised_and_caught(self):
        with pytest.raises(InvalidAPIKeyError) as exc_info:
            raise InvalidAPIKeyError()

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    def test_exception_chain_preserved(self):
        original_error = KeyError("Key not found")

        with pytest.raises(InvalidAPIKeyError) as exc_info:
            try:
                raise original_error
            except KeyError as e:
                raise InvalidAPIKeyError() from e

        assert exc_info.value.__cause__ is original_error


class TestExceptionComparison:
    """Test differences between the two exception types."""

    def test_different_default_messages(self):
        auth_required = AuthenticationRequiredError()
        invalid_key = InvalidAPIKeyError()

        assert auth_required.message != invalid_key.message
        assert auth_required.message == "Authentication required"
        assert invalid_key.message == "Invalid API key"

    def test_different_detail_messages(self):
        auth_required = AuthenticationRequiredError()
        invalid_key = InvalidAPIKeyError()

        assert auth_required.detail != invalid_key.detail
        assert "Provide valid API key" in auth_required.detail
        assert "provided API key is not valid" in invalid_key.detail

    def test_same_status_code(self):
        auth_required = AuthenticationRequiredError()
        invalid_key = InvalidAPIKeyError()

        assert auth_required.status_code == invalid_key.status_code == 401

    def test_both_exceptions_are_distinguishable(self):
        auth_required = AuthenticationRequiredError()
        invalid_key = InvalidAPIKeyError()

        assert type(auth_required) is not type(invalid_key)
        assert isinstance(auth_required, AuthenticationRequiredError)
        assert isinstance(invalid_key, InvalidAPIKeyError)
        assert not isinstance(auth_required, InvalidAPIKeyError)
        assert not isinstance(invalid_key, AuthenticationRequiredError)


class TestExceptionUsageScenarios:
    """Test realistic usage scenarios for both exceptions."""

    def test_authentication_required_scenario(self):
        """Test typical use case for AuthenticationRequiredError."""

        def protected_endpoint(api_key=None):
            if not api_key:
                raise AuthenticationRequiredError()
            return "Success"

        with pytest.raises(AuthenticationRequiredError) as exc_info:
            protected_endpoint()

        error = exc_info.value
        assert error.status_code == 401
        assert "Authentication required" in error.message
        assert "Provide valid API key" in error.detail

    def test_invalid_key_scenario(self):
        """Test typical use case for InvalidAPIKeyError."""

        def validate_api_key(api_key):
            valid_keys = ["valid-key-1", "valid-key-2"]
            if api_key not in valid_keys:
                raise InvalidAPIKeyError()
            return True

        with pytest.raises(InvalidAPIKeyError) as exc_info:
            validate_api_key("invalid-key")

        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in error.message
        assert "provided API key is not valid" in error.detail

    def test_exception_handling_in_auth_flow(self):
        """Test handling both exceptions in authentication flow."""

        def authenticate_request(authorization_header):
            if not authorization_header:
                raise AuthenticationRequiredError()

            api_key = authorization_header.replace("Bearer ", "")
            if api_key != "valid-key":
                raise InvalidAPIKeyError()

            return True

        # Test missing authorization
        with pytest.raises(AuthenticationRequiredError):
            authenticate_request(None)

        # Test invalid key
        with pytest.raises(InvalidAPIKeyError):
            authenticate_request("Bearer invalid-key")

        # Test successful authentication
        assert authenticate_request("Bearer valid-key") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
