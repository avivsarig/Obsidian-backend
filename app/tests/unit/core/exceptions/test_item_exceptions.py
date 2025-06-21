import pytest

from app.src.core.exceptions.base_exceptions import BaseAPIException
from app.src.core.exceptions.item_exceptions import (
    BaseItemException,
    ItemConflictError,
    ItemDateParsingError,
    ItemNotFoundError,
    ItemStateTransitionError,
    ItemValidationError,
)


class TestBaseItemException:
    """Test BaseItemException class."""

    def test_inherits_from_base_api_exception(self):
        """Test that BaseItemException inherits from BaseAPIException."""
        assert issubclass(BaseItemException, BaseAPIException)

    def test_can_be_instantiated(self):
        """Test that BaseItemException can be instantiated."""
        exception = BaseItemException("Test item exception")

        assert isinstance(exception, BaseItemException)
        assert isinstance(exception, BaseAPIException)
        assert exception.message == "Test item exception"

    def test_can_be_raised_and_caught(self):
        """Test that BaseItemException can be raised and caught."""
        with pytest.raises(BaseItemException) as exc_info:
            raise BaseItemException("Test raising")

        assert exc_info.value.message == "Test raising"

    def test_can_be_caught_as_base_api_exception(self):
        """Test that BaseItemException can be caught as BaseAPIException."""
        with pytest.raises(BaseAPIException) as exc_info:
            raise BaseItemException("Test base catching")

        assert isinstance(exc_info.value, BaseItemException)


class TestItemNotFoundError:
    """Test ItemNotFoundError class."""

    def test_inherits_from_base_item_exception(self):
        """Test that ItemNotFoundError inherits from BaseItemException."""
        assert issubclass(ItemNotFoundError, BaseItemException)
        assert issubclass(ItemNotFoundError, BaseAPIException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = ItemNotFoundError("Custom not found message")

        assert exception.message == "Custom not found message"
        assert exception.status_code == 404
        assert "may have been moved, deleted" in exception.detail
        assert exception.item_type is None
        assert exception.item_id is None

    def test_constructor_with_item_type_and_id(self):
        """Test creating exception with item_type and item_id for smart message."""
        exception = ItemNotFoundError(item_type="task", item_id="123")

        assert exception.message == "Task '123' not found"
        assert exception.status_code == 404
        assert exception.item_type == "task"
        assert exception.item_id == "123"

    def test_constructor_with_item_type_and_id_lowercase(self):
        """Test that item_type is properly capitalized in message."""
        exception = ItemNotFoundError(item_type="user", item_id="abc-def")

        assert exception.message == "User 'abc-def' not found"
        assert exception.item_type == "user"
        assert exception.item_id == "abc-def"

    def test_constructor_without_message_or_item_info(self):
        """Test creating exception without message or item info uses default."""
        exception = ItemNotFoundError()

        assert exception.message == "Requested item not found"
        assert exception.status_code == 404
        assert exception.item_type is None
        assert exception.item_id is None

    def test_constructor_with_custom_detail(self):
        """Test creating exception with custom detail."""
        custom_detail = "This specific item was archived"
        exception = ItemNotFoundError("Not found", detail=custom_detail)

        assert exception.detail == custom_detail

    def test_constructor_with_partial_item_info(self):
        """Test creating exception with only item_type or only item_id."""
        # Only item_type
        exception1 = ItemNotFoundError(item_type="project")
        assert exception1.message == "Requested item not found"
        assert exception1.item_type == "project"
        assert exception1.item_id is None

        # Only item_id
        exception2 = ItemNotFoundError(item_id="999")
        assert exception2.message == "Requested item not found"
        assert exception2.item_type is None
        assert exception2.item_id == "999"

    def test_constructor_explicit_message_overrides_smart_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = ItemNotFoundError(
            message="Explicit message", item_type="task", item_id="123"
        )

        assert exception.message == "Explicit message"
        assert exception.item_type == "task"
        assert exception.item_id == "123"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = ItemNotFoundError(
            message="Custom message",
            detail="Custom detail",
            item_type="document",
            item_id="doc-456",
        )

        assert exception.message == "Custom message"
        assert exception.detail == "Custom detail"
        assert exception.status_code == 404
        assert exception.item_type == "document"
        assert exception.item_id == "doc-456"


class TestItemValidationError:
    """Test ItemValidationError class."""

    def test_inherits_from_base_item_exception(self):
        """Test that ItemValidationError inherits from BaseItemException."""
        assert issubclass(ItemValidationError, BaseItemException)

    def test_constructor_with_message_only(self):
        """Test creating exception with only message."""
        exception = ItemValidationError("Validation failed")

        assert exception.message == "Validation failed"
        assert exception.status_code == 400
        assert exception.detail == "Check item for missing fields"
        assert exception.field is None
        assert exception.value is None
        assert exception.errors == []

    def test_constructor_with_field_generates_detail(self):
        """Test that providing field generates appropriate detail."""
        exception = ItemValidationError("Invalid field", field="email")

        assert exception.message == "Invalid field"
        assert exception.detail == "Validation failed for field: email"
        assert exception.field == "email"

    def test_constructor_with_errors_list_generates_detail(self):
        """Test that providing errors list generates appropriate detail."""
        errors = ["error1", "error2", "error3"]
        exception = ItemValidationError("Multiple errors", errors=errors)

        assert exception.message == "Multiple errors"
        assert exception.detail == "Multiple validation errors: 3 fields"
        assert exception.errors == errors

    def test_constructor_with_field_and_value(self):
        """Test creating exception with field and value."""
        exception = ItemValidationError(
            "Invalid email format", field="email", value="not-an-email"
        )

        assert exception.field == "email"
        assert exception.value == "not-an-email"
        assert exception.detail == "Validation failed for field: email"

    def test_constructor_with_custom_detail_gets_overridden_by_field(self):
        """Test that field generation overrides custom detail."""
        exception = ItemValidationError(
            "Custom validation error", detail="Custom detail message", field="username"
        )

        # Field takes priority and overrides custom detail
        assert exception.detail == "Validation failed for field: username"
        assert exception.field == "username"

    def test_constructor_with_custom_detail_only(self):
        """Test that custom detail is preserved when no field/errors provided."""
        exception = ItemValidationError(
            "Custom validation error", detail="Custom detail message"
        )

        # No field or errors, so custom detail should be preserved
        assert exception.detail == "Custom detail message"
        assert exception.field is None
        assert exception.errors == []

    def test_constructor_with_all_parameters(self):
        """Test creating exception with all parameters."""
        errors = ["Missing required field", "Invalid format"]
        exception = ItemValidationError(
            message="Comprehensive validation error",
            detail="Custom detail",
            field="password",
            value="weak",
            errors=errors,
        )

        assert exception.message == "Comprehensive validation error"
        # Field takes priority over custom detail
        assert exception.detail == "Validation failed for field: password"
        assert exception.field == "password"
        assert exception.value == "weak"
        assert exception.errors == errors

    def test_errors_defaults_to_empty_list(self):
        """Test that errors defaults to empty list when None."""
        exception = ItemValidationError("Test", errors=None)

        assert exception.errors == []

    def test_field_priority_over_errors_for_detail(self):
        """Test that field takes priority over errors for detail generation."""
        errors = ["error1", "error2"]
        exception = ItemValidationError(
            "Test message", field="priority_field", errors=errors
        )

        assert exception.detail == "Validation failed for field: priority_field"
        assert exception.field == "priority_field"
        assert exception.errors == errors


class TestItemDateParsingError:
    """Test ItemDateParsingError class."""

    def test_inherits_from_item_validation_error(self):
        """Test that ItemDateParsingError inherits from ItemValidationError."""
        assert issubclass(ItemDateParsingError, ItemValidationError)
        assert issubclass(ItemDateParsingError, BaseItemException)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = ItemDateParsingError("Custom date error")

        assert exception.message == "Custom date error"
        assert exception.status_code == 400
        assert exception.date_string is None

    def test_constructor_with_date_string_generates_message(self):
        """Test that providing date_string generates appropriate message."""
        exception = ItemDateParsingError(date_string="invalid-date")

        assert exception.message == "Invalid date format: 'invalid-date'"
        assert exception.date_string == "invalid-date"

    def test_constructor_without_message_or_date_string(self):
        """Test creating exception without message or date_string uses default."""
        exception = ItemDateParsingError()

        assert exception.message == "Date format is invalid"
        assert exception.date_string is None

    def test_constructor_with_field_parameter(self):
        """Test creating exception with field parameter."""
        exception = ItemDateParsingError(date_string="2023-13-45", field="due_date")

        assert exception.message == "Invalid date format: '2023-13-45'"
        assert exception.field == "due_date"
        assert exception.value == "2023-13-45"
        assert exception.date_string == "2023-13-45"

    def test_constructor_explicit_message_overrides_generation(self):
        """Test that explicit message overrides generation."""
        exception = ItemDateParsingError(
            message="Explicit date error", date_string="bad-date"
        )

        assert exception.message == "Explicit date error"
        assert exception.date_string == "bad-date"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = ItemDateParsingError(
            message="Custom date parsing error",
            date_string="2023-99-99",
            field="created_at",
        )

        assert exception.message == "Custom date parsing error"
        assert exception.date_string == "2023-99-99"
        assert exception.field == "created_at"
        assert exception.value == "2023-99-99"

    def test_inherits_validation_error_behavior(self):
        """Test that it inherits ItemValidationError behavior."""
        exception = ItemDateParsingError("Date error", field="timestamp")

        # Should have validation error detail generation
        assert exception.detail == "Validation failed for field: timestamp"
        assert exception.status_code == 400


class TestItemStateTransitionError:
    """Test ItemStateTransitionError class."""

    def test_inherits_from_item_validation_error(self):
        """Test that ItemStateTransitionError inherits from ItemValidationError."""
        assert issubclass(ItemStateTransitionError, ItemValidationError)

    def test_constructor_with_explicit_message(self):
        """Test creating exception with explicit message."""
        exception = ItemStateTransitionError("Custom state error")

        assert exception.message == "Custom state error"
        assert exception.status_code == 400

    def test_constructor_with_state_info_generates_message(self):
        """Test that providing state info generates appropriate message."""
        exception = ItemStateTransitionError(
            item_type="task", current_state="completed", attempted_action="delete"
        )

        assert exception.message == "Cannot delete task in completed state"
        assert exception.item_type == "task"
        assert exception.current_state == "completed"
        assert exception.attempted_action == "delete"

    def test_constructor_without_message_or_state_info(self):
        """Test creating exception without message or state info uses default."""
        exception = ItemStateTransitionError()

        assert exception.message == "Invalid state transition attempted"
        assert exception.item_type is None
        assert exception.current_state is None
        assert exception.attempted_action is None

    def test_constructor_with_partial_state_info(self):
        """Test creating exception with partial state info uses default message."""
        # Missing attempted_action
        exception1 = ItemStateTransitionError(
            item_type="document", current_state="draft"
        )
        assert exception1.message == "Invalid state transition attempted"

        # Missing current_state
        exception2 = ItemStateTransitionError(
            item_type="task", attempted_action="archive"
        )
        assert exception2.message == "Invalid state transition attempted"

    def test_constructor_with_custom_detail(self):
        """Test creating exception with custom detail."""
        exception = ItemStateTransitionError(
            "State error", detail="Custom transition detail"
        )

        assert exception.detail == "Custom transition detail"

    def test_constructor_default_detail(self):
        """Test that default detail is set when none provided."""
        exception = ItemStateTransitionError("State error")

        assert "Check the current state and allowed transitions" in exception.detail

    def test_explicit_message_overrides_generation(self):
        """Test that explicit message overrides smart generation."""
        exception = ItemStateTransitionError(
            message="Explicit state error",
            item_type="project",
            current_state="active",
            attempted_action="start",
        )

        assert exception.message == "Explicit state error"
        assert exception.item_type == "project"

    def test_all_parameters_together(self):
        """Test creating exception with all parameters."""
        exception = ItemStateTransitionError(
            message="Custom state transition error",
            detail="Custom detail",
            item_type="workflow",
            current_state="pending",
            attempted_action="cancel",
        )

        assert exception.message == "Custom state transition error"
        assert exception.detail == "Custom detail"
        assert exception.item_type == "workflow"
        assert exception.current_state == "pending"
        assert exception.attempted_action == "cancel"


class TestItemConflictError:
    """Test ItemConflictError class."""

    def test_inherits_from_base_item_exception(self):
        """Test that ItemConflictError inherits from BaseItemException."""
        assert issubclass(ItemConflictError, BaseItemException)

    def test_constructor_with_message_only(self):
        """Test creating exception with only message."""
        exception = ItemConflictError("Conflict detected")

        assert exception.message == "Conflict detected"
        assert exception.status_code == 409
        assert exception.detail == "Resolve the conflict and try again"
        assert exception.conflicting_field is None
        assert exception.conflicting_value is None

    def test_constructor_with_conflicting_field(self):
        """Test creating exception with conflicting field."""
        exception = ItemConflictError(
            "Username already exists", conflicting_field="username"
        )

        assert exception.message == "Username already exists"
        assert exception.conflicting_field == "username"

    def test_constructor_with_conflicting_value(self):
        """Test creating exception with conflicting value."""
        exception = ItemConflictError(
            "Email conflict", conflicting_value="user@example.com"
        )

        assert exception.conflicting_value == "user@example.com"

    def test_constructor_with_field_and_value(self):
        """Test creating exception with both field and value."""
        exception = ItemConflictError(
            "Duplicate entry detected",
            conflicting_field="email",
            conflicting_value="test@example.com",
        )

        assert exception.conflicting_field == "email"
        assert exception.conflicting_value == "test@example.com"

    def test_conflicting_value_can_be_any_type(self):
        """Test that conflicting_value can be any type."""
        # Test with different types
        test_values = [123, ["list", "value"], {"dict": "value"}, None, True]

        for value in test_values:
            exception = ItemConflictError("Type test", conflicting_value=value)
            assert exception.conflicting_value == value

    def test_status_code_is_409(self):
        """Test that status code is always 409 for conflicts."""
        exception = ItemConflictError("Any conflict message")

        assert exception.status_code == 409

    def test_default_detail_message(self):
        """Test that default detail message is consistent."""
        exception = ItemConflictError("Conflict")

        assert exception.detail == "Resolve the conflict and try again"


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance relationships."""

    def test_inheritance_chain(self):
        """Test the complete inheritance chain."""
        # BaseItemException -> BaseAPIException -> Exception
        assert issubclass(BaseItemException, BaseAPIException)
        assert issubclass(BaseAPIException, Exception)

        # ItemNotFoundError -> BaseItemException
        assert issubclass(ItemNotFoundError, BaseItemException)

        # ItemValidationError -> BaseItemException
        assert issubclass(ItemValidationError, BaseItemException)

        # ItemDateParsingError -> ItemValidationError
        assert issubclass(ItemDateParsingError, ItemValidationError)

        # ItemStateTransitionError -> ItemValidationError
        assert issubclass(ItemStateTransitionError, ItemValidationError)

        # ItemConflictError -> BaseItemException
        assert issubclass(ItemConflictError, BaseItemException)

    def test_all_item_exceptions_can_be_caught_as_base_item_exception(self):
        """Test that all item exceptions can be caught as BaseItemException."""
        exceptions = [
            ItemNotFoundError("Not found"),
            ItemValidationError("Validation error"),
            ItemDateParsingError("Date error"),
            ItemStateTransitionError("State error"),
            ItemConflictError("Conflict error"),
        ]

        for exc in exceptions:
            with pytest.raises(BaseItemException):
                raise exc

    def test_validation_errors_can_be_caught_as_item_validation_error(self):
        """Test that validation-related errors can be caught as ItemValidationError."""
        validation_exceptions = [
            ItemValidationError("Basic validation"),
            ItemDateParsingError("Date validation"),
            ItemStateTransitionError("State validation"),
        ]

        for exc in validation_exceptions:
            with pytest.raises(ItemValidationError):
                raise exc

    def test_status_codes_are_inherited_correctly(self):
        """Test that status codes are set correctly in the hierarchy."""
        # 404 for not found
        not_found = ItemNotFoundError("Not found")
        assert not_found.status_code == 404

        # 400 for validation errors
        validation = ItemValidationError("Validation")
        assert validation.status_code == 400

        date_parsing = ItemDateParsingError("Date error")
        assert date_parsing.status_code == 400

        state_transition = ItemStateTransitionError("State error")
        assert state_transition.status_code == 400

        # 409 for conflicts
        conflict = ItemConflictError("Conflict")
        assert conflict.status_code == 409

    def test_base_api_exception_attributes_preserved(self):
        """Test that BaseAPIException attributes are preserved."""
        exception = ItemNotFoundError("Test", item_type="task", item_id="123")

        # Should have BaseAPIException attributes
        assert hasattr(exception, "message")
        assert hasattr(exception, "status_code")
        assert hasattr(exception, "detail")
        assert hasattr(exception, "should_alert")

        # Should also have item-specific attributes
        assert hasattr(exception, "item_type")
        assert hasattr(exception, "item_id")


class TestExceptionIntegration:
    """Test integration scenarios and real-world usage patterns."""

    def test_exception_serialization_compatibility(self):
        """Test that exceptions work with string representation."""
        exceptions = [
            ItemNotFoundError("Task not found"),
            ItemValidationError("Invalid email"),
            ItemDateParsingError("Bad date format"),
            ItemStateTransitionError("Cannot transition"),
            ItemConflictError("Username exists"),
        ]

        for exc in exceptions:
            assert str(exc) == exc.message
            assert repr(exc)  # Should not raise

    def test_exception_with_original_error_chaining(self):
        """Test exception chaining works with item exceptions using BaseAPIException."""
        try:
            raise ValueError("Database connection failed")
        except ValueError as original:
            # Item exceptions don't expose original_error in constructor
            # but we can test that they inherit from BaseAPIException
            # which supports original error chaining
            from app.src.core.exceptions.base_exceptions import BaseAPIException

            base_exception = BaseAPIException(
                "Item not found due to database error", original_error=original
            )

            assert base_exception.__cause__ is original

            # And test that item exceptions are indeed BaseAPIExceptions
            item_exception = ItemNotFoundError("Test")
            assert isinstance(item_exception, BaseAPIException)

    def test_realistic_usage_scenarios(self):
        """Test realistic usage scenarios for each exception type."""
        # Not found scenario
        task_not_found = ItemNotFoundError(item_type="task", item_id="task-123")
        assert task_not_found.message == "Task 'task-123' not found"
        assert task_not_found.status_code == 404

        # Validation scenario
        email_validation = ItemValidationError(
            "Invalid email format", field="email", value="not-an-email"
        )
        assert email_validation.status_code == 400
        assert "email" in email_validation.detail

        # Date parsing scenario
        date_error = ItemDateParsingError(date_string="2023-13-45", field="due_date")
        assert "Invalid date format" in date_error.message
        assert date_error.field == "due_date"

        # State transition scenario
        state_error = ItemStateTransitionError(
            item_type="task", current_state="completed", attempted_action="edit"
        )
        assert state_error.message == "Cannot edit task in completed state"

        # Conflict scenario
        conflict_error = ItemConflictError(
            "Email already registered",
            conflicting_field="email",
            conflicting_value="user@example.com",
        )
        assert conflict_error.status_code == 409


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
