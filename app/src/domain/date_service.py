from datetime import date, datetime, time

from app.src.domain.value_objects import DateValue, ParsedDate


class DateService:
    """Service for parsing, normalizing, and formatting dates for task management.

    Provides field-specific date handling with different semantics:
    - due_date: defaults to end of day (23:59:59)
    - do_date: defaults to start of day (00:00:00)
    - completed_at: uses current time when no time specified
    """

    # Supported date formats in order of preference
    DATE_FORMATS = [
        "%Y-%m-%dT%H:%M:%S",  # Full datetime
        "%Y-%m-%dT%H:%M",  # DateTime without seconds
        "%Y-%m-%d",  # Date only
    ]

    # Field-specific time defaults
    FIELD_TIME_DEFAULTS = {
        "due_date": time(23, 59, 59),  # End of day for deadlines
        "do_date": time(0, 0, 0),  # Start of day for tasks
    }

    def __init__(self) -> None:
        """Initialize the DateService with default formats and field mappings."""
        self.formats = self.DATE_FORMATS

    def parse_date_string(
        self,
        date_str: str,
    ) -> ParsedDate:
        """Parse a date string into a datetime object using supported formats.

        Args:
            date_str: Date string to parse

        Returns:
            Parsed datetime object or None if empty string

        Raises:
            ValueError: If date string format is not recognized
        """
        if not date_str or not date_str.strip():
            return None

        for fmt in self.formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Invalid date format: {date_str}")

    def normalize_for_field(
        self,
        value: DateValue,
        field_name: str,
    ) -> ParsedDate:
        """Normalize a date value for a specific field with appropriate semantics.

        Args:
            value: Date value to normalize (string, datetime, date, or None)
            field_name: Target field name for semantic interpretation

        Returns:
            Normalized datetime object or None
        """
        if not value:
            return None

        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return self._date_to_datetime(value, field_name)
        elif isinstance(value, str):
            parsed = self.parse_date_string(value)
            return self._apply_field_semantics(
                parsed, field_name, has_time="T" in value
            )
        else:
            return None

    @staticmethod
    def now_timestamp_str() -> str:
        """Get current timestamp as ISO format string.

        Returns:
            Current datetime formatted as YYYY-MM-DDTHH:MM:SS
        """
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def _get_field_time(
        self,
        field_name: str,
    ) -> time:
        """Get default time for a specific field.

        Args:
            field_name: Name of the field

        Returns:
            Default time object for the field
        """
        return self.FIELD_TIME_DEFAULTS.get(field_name, time(0, 0, 0))

    def _date_to_datetime(
        self,
        date_obj: date,
        field_name: str,
    ) -> datetime:
        """Convert a date object to datetime using field-specific time defaults.

        Args:
            date_obj: Date to convert
            field_name: Field name for time semantics

        Returns:
            Datetime object with appropriate time component
        """
        field_time = self._get_field_time(field_name)
        return datetime.combine(date_obj, field_time)

    def _apply_field_semantics(
        self,
        dt: ParsedDate,
        field_name: str,
        has_time: bool,
    ) -> ParsedDate:
        """Apply field-specific semantic rules to a datetime.

        Args:
            dt: Datetime to modify
            field_name: Field name for semantic rules
            has_time: Whether original input had time component

        Returns:
            Datetime with field semantics applied
        """
        if not dt:
            return None

        if has_time:
            return dt

        # Special case: completion times use current time if no time specified
        if field_name == "completed_at":
            now = datetime.now()
            return dt.replace(
                hour=now.hour,
                minute=now.minute,
                second=now.second,
            )

        field_time = self._get_field_time(field_name)
        return dt.replace(
            hour=field_time.hour,
            minute=field_time.minute,
            second=field_time.second,
        )

    def format_for_storage(self, dt: datetime, field_name: str) -> str:
        """Format datetime for storage based on field semantics.

        Args:
            dt: Datetime to format
            field_name: Field name for format selection

        Returns:
            Formatted date string appropriate for storage
        """
        if isinstance(dt, str):
            return dt

        if field_name == "completed_at":
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

        if self._is_date_only_semantics(dt, field_name):
            return dt.strftime("%Y-%m-%d")
        else:
            return dt.strftime("%Y-%m-%dT%H:%M")

    def _is_date_only_semantics(self, dt: datetime, field_name: str) -> bool:
        """Check if datetime represents date-only semantics for a field.

        Args:
            dt: Datetime to check
            field_name: Field name for semantic comparison

        Returns:
            True if datetime matches field's default time
        """
        expected_time = self._get_field_time(field_name)

        return (
            dt.hour == expected_time.hour
            and dt.minute == expected_time.minute
            and dt.second == expected_time.second
        )


_date_service = DateService()


def get_date_service() -> DateService:
    """Get the singleton DateService instance.

    Returns:
        Global DateService instance
    """
    return _date_service


def normalize_date_field(value: DateValue, field_name: str = "") -> ParsedDate:
    """Convenience function to normalize a date value for a field.

    Args:
        value: Date value to normalize
        field_name: Target field name

    Returns:
        Normalized datetime object
    """
    return get_date_service().normalize_for_field(value, field_name)


def parse_date_string(date_str: str) -> ParsedDate:
    """Convenience function to parse a date string.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime object
    """
    return get_date_service().parse_date_string(date_str)
