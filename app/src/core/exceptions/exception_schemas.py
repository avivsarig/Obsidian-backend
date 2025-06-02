from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    detail: Optional[str] = Field(None, description="Additional error details")

    path: Optional[str] = Field(None, description="Request path (development only)")
    method: Optional[str] = Field(None, description="HTTP method (development only)")
    original_error: Optional[dict[str, str]] = Field(
        None, description="Original exception details (development only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Task 'daily-review' not found",
                "status_code": 404,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "detail": "The item may have been moved, deleted, "
                "or you may not have access to it",
            }
        }


class ValidationErrorResponse(ErrorResponse):
    field: Optional[str] = Field(None, description="Field that failed validation")
    value: Optional[str] = Field(None, description="Invalid value that was provided")
    errors: Optional[list[str]] = Field(None, description="List of validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid date format: '2024-13-45'",
                "status_code": 400,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "detail": "Validation failed for field: due_date",
                "field": "due_date",
                "value": "2024-13-45",
            }
        }


class ServerErrorResponse(ErrorResponse):
    exception_type: Optional[str] = Field(
        None, description="Exception type (development only)"
    )
    exception_message: Optional[str] = Field(
        None, description="Exception message (development only)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Internal server error",
                "status_code": 500,
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "detail": "An unexpected error occurred. Please try again.",
            }
        }
