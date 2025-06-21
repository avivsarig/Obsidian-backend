import pytest

from app.src.core.exceptions.base_exceptions import BaseAPIException


class TestBaseAPIException:
    """Test BaseAPIException class."""

    def test_constructor_with_message_only(self):
        """Test creating exception with only required message parameter."""
        message = "Test error message"
        exception = BaseAPIException(message)

        assert exception.message == message
        assert exception.status_code == 500  # Default value
        assert exception.detail is None  # Default value
        assert exception.should_alert is False  # Default value
        assert exception.__cause__ is None  # No original error

    def test_constructor_with_all_parameters(self):
        """Test creating exception with all parameters provided."""
        message = "Comprehensive error"
        status_code = 404
        detail = "Resource not found in database"
        original_error = ValueError("Invalid input")
        should_alert = True

        exception = BaseAPIException(
            message=message,
            status_code=status_code,
            detail=detail,
            original_error=original_error,
            should_alert=should_alert,
        )

        assert exception.message == message
        assert exception.status_code == status_code
        assert exception.detail == detail
        assert exception.should_alert == should_alert
        assert exception.__cause__ is original_error

    def test_constructor_with_custom_status_code(self):
        """Test creating exception with custom status code."""
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
            assert exception.status_code == status_code
            assert exception.message == message

    def test_constructor_with_detail(self):
        """Test creating exception with detail information."""
        message = "Validation failed"
        detail = "Field 'email' is required but was not provided"

        exception = BaseAPIException(message, detail=detail)

        assert exception.message == message
        assert exception.detail == detail
        assert exception.status_code == 500  # Default

    def test_constructor_with_should_alert_true(self):
        """Test creating exception with should_alert set to True."""
        message = "Critical system error"
        exception = BaseAPIException(message, should_alert=True)

        assert exception.message == message
        assert exception.should_alert is True

    def test_constructor_with_should_alert_false(self):
        """Test creating exception with should_alert explicitly set to False."""
        message = "Non-critical error"
        exception = BaseAPIException(message, should_alert=False)

        assert exception.message == message
        assert exception.should_alert is False

    def test_original_error_sets_cause(self):
        """Test that providing original_error sets __cause__ correctly."""
        original_error = RuntimeError("Database connection failed")
        exception = BaseAPIException(
            "Service unavailable", original_error=original_error
        )

        assert exception.__cause__ is original_error

    def test_no_original_error_no_cause(self):
        """Test that without original_error, __cause__ remains None."""
        exception = BaseAPIException("Simple error")

        assert exception.__cause__ is None

    def test_inheritance_from_exception(self):
        """Test that BaseAPIException properly inherits from Exception."""
        exception = BaseAPIException("Test inheritance")

        assert isinstance(exception, Exception)
        assert isinstance(exception, BaseAPIException)
        assert issubclass(BaseAPIException, Exception)

    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught properly."""
        message = "Test exception raising"

        with pytest.raises(BaseAPIException) as exc_info:
            raise BaseAPIException(message)

        assert exc_info.value.message == message
        assert str(exc_info.value) == message

    def test_can_be_caught_as_exception(self):
        """Test that BaseAPIException can be caught as generic Exception."""
        message = "Test generic catching"

        with pytest.raises(Exception) as exc_info:
            raise BaseAPIException(message)

        assert isinstance(exc_info.value, BaseAPIException)
        assert str(exc_info.value) == message

    def test_string_representation(self):
        """Test string representation of the exception."""
        message = "String representation test"
        exception = BaseAPIException(message)

        assert str(exception) == message

    def test_string_representation_with_details(self):
        """Test string representation includes the message."""
        message = "Error with details"
        detail = "Additional context"
        exception = BaseAPIException(message, detail=detail)

        # The string representation should be the message
        assert str(exception) == message

    def test_repr_representation(self):
        """Test repr representation of the exception."""
        message = "Repr test"
        exception = BaseAPIException(message)

        repr_str = repr(exception)
        assert "BaseAPIException" in repr_str
        assert message in repr_str

    def test_empty_string_message(self):
        """Test creating exception with empty string message."""
        exception = BaseAPIException("")

        assert exception.message == ""
        assert str(exception) == ""

    def test_none_detail_explicitly(self):
        """Test creating exception with explicitly None detail."""
        exception = BaseAPIException("Test", detail=None)

        assert exception.detail is None

    def test_none_original_error_explicitly(self):
        """Test creating exception with explicitly None original_error."""
        exception = BaseAPIException("Test", original_error=None)

        assert exception.__cause__ is None

    def test_exception_chaining_preserves_traceback(self):
        """Test that exception chaining preserves the original traceback."""
        try:
            # Create an original error with a traceback
            raise ValueError("Original error")
        except ValueError as e:
            # Chain it with BaseAPIException
            chained_exception = BaseAPIException("Chained error", original_error=e)

            assert chained_exception.__cause__ is e
            assert chained_exception.__cause__.__traceback__ is not None

    def test_multiple_instances_are_independent(self):
        """Test that multiple instances don't share state."""
        exception1 = BaseAPIException("Error 1", status_code=400)
        exception2 = BaseAPIException("Error 2", status_code=404)

        assert exception1.message != exception2.message
        assert exception1.status_code != exception2.status_code
        assert exception1 is not exception2

    def test_attribute_modification_after_creation(self):
        """Test that attributes can be modified after creation."""
        exception = BaseAPIException("Original message")

        # Modify attributes
        exception.message = "Modified message"
        exception.status_code = 418
        exception.detail = "Added detail"
        exception.should_alert = True

        assert exception.message == "Modified message"
        assert exception.status_code == 418
        assert exception.detail == "Added detail"
        assert exception.should_alert is True

    def test_with_different_exception_types_as_original_error(self):
        """Test with various exception types as original_error."""
        original_errors = [
            ValueError("Value error"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
        ]

        for original_error in original_errors:
            exception = BaseAPIException("Wrapper error", original_error=original_error)
            assert exception.__cause__ is original_error
            assert isinstance(exception.__cause__, type(original_error))

    def test_boolean_evaluation(self):
        """Test that exception evaluates to True in boolean context."""
        exception = BaseAPIException("Test")

        assert bool(exception) is True

    def test_equality_and_identity(self):
        """Test equality and identity behavior."""
        message = "Same message"
        exception1 = BaseAPIException(message)
        exception2 = BaseAPIException(message)

        # Different instances are not identical
        assert exception1 is not exception2

        # But they are equal if they have the same message
        # (Exception base class handles equality by message)
        assert exception1.args == exception2.args

    def test_args_attribute(self):
        """Test that args attribute is set correctly."""
        message = "Test args"
        exception = BaseAPIException(message)

        # Exception base class sets args from the message
        assert exception.args == (message,)

    def test_comprehensive_scenario(self):
        """Test a comprehensive real-world scenario."""
        # Simulate a database connection error
        try:
            raise ConnectionError("Database connection timeout")
        except ConnectionError as db_error:
            # Wrap it in our custom exception
            api_exception = BaseAPIException(
                message="Service temporarily unavailable",
                status_code=503,
                detail="Database connection failed after 30 second timeout",
                original_error=db_error,
                should_alert=True,
            )

            # Verify all attributes
            assert api_exception.message == "Service temporarily unavailable"
            assert api_exception.status_code == 503
            assert (
                api_exception.detail
                == "Database connection failed after 30 second timeout"
            )
            assert api_exception.should_alert is True
            assert api_exception.__cause__ is db_error
            assert isinstance(api_exception.__cause__, ConnectionError)

            # Verify it can be raised and caught
            with pytest.raises(BaseAPIException) as exc_info:
                raise api_exception  # noqa: B904

            caught_exception = exc_info.value
            assert caught_exception is api_exception
            assert caught_exception.__cause__ is db_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
