from datetime import date, datetime, time

from app.src.domain.value_objects import DateValue, ParsedDate


class DateService:
    def __init__(self):
        self.formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
        ]

    def parse_datevalue_to_parseddate(
        self,
        date_str: str,
    ) -> ParsedDate:
        if not date_str or date_str == "":
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
        if not value:
            return None

        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return self._date_to_datetime(value, field_name)
        elif isinstance(value, str):
            parsed = self.parse_datevalue_to_parseddate(value)
            return self._apply_field_semantics(
                parsed, field_name, has_time="T" in value
            )
        else:
            return None

    def _get_field_time(
        self,
        field_name: str,
    ) -> time:
        field_times = {
            "due_date": time(23, 59, 59),  # End of day for deadlines
            "do_date": time(0, 0, 0),  # Start of day for tasks
        }
        return field_times.get(field_name, time(0, 0, 0))

    def _date_to_datetime(
        self,
        date_obj: date,
        field_name: str,
    ) -> datetime:
        field_time = self._get_field_time(field_name)
        return datetime.combine(date_obj, field_time)

    def _apply_field_semantics(
        self,
        dt: ParsedDate,
        field_name: str,
        has_time: bool,
    ) -> ParsedDate:
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
        if isinstance(dt, str):
            return dt

        if field_name == "completed_at":
            return dt.strftime("%Y-%m-%dT%H:%M:%S")

        if self._is_date_only_semantics(dt, field_name):
            return dt.strftime("%Y-%m-%d")
        else:
            return dt.strftime("%Y-%m-%dT%H:%M")

    def _is_date_only_semantics(self, dt: datetime, field_name: str) -> bool:
        expected_time = self._get_field_time(field_name)

        return (
            dt.hour == expected_time.hour
            and dt.minute == expected_time.minute
            and dt.second == expected_time.second
        )


_date_service = DateService()


def get_date_service() -> DateService:
    return _date_service


def normalize_date_field(value: DateValue, field_name: str = "") -> ParsedDate:
    return get_date_service().normalize_for_field(value, field_name)


def parse_date_string(date_str: str) -> ParsedDate:
    return get_date_service().parse_datevalue_to_parseddate(date_str)
