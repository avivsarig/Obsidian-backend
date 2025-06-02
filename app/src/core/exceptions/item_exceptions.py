from typing import Any

from app.src.core.exceptions.base_exceptions import BaseAPIException


class BaseItemException(BaseAPIException):
    pass


class ItemNotFoundError(BaseItemException):
    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
        item_type: str | None = None,
        item_id: str | None = None,
    ):
        if message is None and item_type and item_id:
            message = f"{item_type.title()} '{item_id}' not found"
        elif message is None:
            message = "Requested item not found"

        super().__init__(
            message,
            status_code=404,
            detail=detail
            or (
                "The item may have been moved, deleted, "
                "or you may not have access to it"
            ),
        )
        self.item_type = item_type
        self.item_id = item_id


class ItemValidationError(BaseItemException):
    def __init__(
        self,
        message: str,
        detail: str | None = None,
        field: str | None = None,
        value: Any = None,
        errors: list | None = None,
    ):
        if field:
            detail = f"Validation failed for field: {field}"
        elif errors:
            detail = f"Multiple validation errors: {len(errors)} fields"

        super().__init__(
            message,
            status_code=400,
            detail=detail or "Check item for missing fields",
        )
        self.field = field
        self.value = value
        self.errors = errors or []


class ItemDateParsingError(ItemValidationError):
    def __init__(
        self,
        message: str | None = None,
        date_string: str | None = None,
        field: str | None = None,
    ):
        if message is None and date_string:
            message = f"Invalid date format: '{date_string}'"
        elif message is None:
            message = "Date format is invalid"

        super().__init__(
            message,
            field=field,
            value=date_string,
        )
        self.date_string = date_string


class ItemStateTransitionError(ItemValidationError):
    def __init__(
        self,
        message: str | None = None,
        detail: str | None = None,
        item_type: str | None = None,
        current_state: str | None = None,
        attempted_action: str | None = None,
    ):
        if message is None and all([item_type, current_state, attempted_action]):
            message = f"Cannot {attempted_action} {item_type} in {current_state} state"
        elif message is None:
            message = "Invalid state transition attempted"

        super().__init__(
            message,
            detail=detail
            or "Check the current state and allowed transitions for this item type",
        )
        self.item_type = item_type
        self.current_state = current_state
        self.attempted_action = attempted_action


class ItemConflictError(BaseItemException):
    def __init__(
        self,
        message: str,
        conflicting_field: str | None = None,
        conflicting_value: Any = None,
    ):
        super().__init__(
            message,
            status_code=409,
            detail="Resolve the conflict and try again",
        )
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value
