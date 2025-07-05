from datetime import date, datetime, time
from unittest.mock import patch

import pytest

from app.src.domain.date_service import (
    DateService,
    get_date_service,
    normalize_date_field,
    parse_date_string,
)


class TestDateServiceInitialization:
    """Test DateService initialization and constants."""

    def test_initialization(self):
        """Test DateService initializes with correct formats."""
        service = DateService()

        expected_formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
        ]
        assert service.formats == expected_formats

    def test_constants(self):
        """Test class constants are properly defined."""
        assert DateService.DATE_FORMATS == [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
        ]

        expected_defaults = {
            "due_date": time(23, 59, 59),
            "do_date": time(0, 0, 0),
        }
        assert DateService.FIELD_TIME_DEFAULTS == expected_defaults


class TestDateStringParsing:
    """Test date string parsing functionality."""

    def test_parse_full_datetime(self):
        """Test parsing full datetime format."""
        service = DateService()
        result = service.parse_date_string("2025-01-15T14:30:45")

        expected = datetime(2025, 1, 15, 14, 30, 45)
        assert result == expected

    def test_parse_datetime_without_seconds(self):
        """Test parsing datetime without seconds."""
        service = DateService()
        result = service.parse_date_string("2025-01-15T14:30")

        expected = datetime(2025, 1, 15, 14, 30, 0)
        assert result == expected

    def test_parse_date_only(self):
        """Test parsing date-only format."""
        service = DateService()
        result = service.parse_date_string("2025-01-15")

        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        service = DateService()
        assert service.parse_date_string("") is None
        assert service.parse_date_string("   ") is None

    def test_parse_none_string(self):
        """Test parsing None returns None."""
        service = DateService()
        assert service.parse_date_string(None) is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises ValueError."""
        service = DateService()

        with pytest.raises(ValueError, match="Invalid date format: invalid-date"):
            service.parse_date_string("invalid-date")

    def test_parse_malformed_date(self):
        """Test parsing malformed but format-matching date raises ValueError."""
        service = DateService()

        with pytest.raises(ValueError, match="Invalid date format: 2025-13-32"):
            service.parse_date_string("2025-13-32")

    def test_parse_format_priority(self):
        """Test that formats are tried in priority order."""
        service = DateService()

        # This should match the first format pattern, not the third
        result = service.parse_date_string("2025-01-15T14:30:45")
        assert result == datetime(2025, 1, 15, 14, 30, 45)


class TestFieldNormalization:
    """Test field-specific date normalization."""

    def test_normalize_none_value(self):
        """Test normalizing None value returns None."""
        service = DateService()
        assert service.normalize_for_field(None, "due_date") is None

    def test_normalize_empty_string(self):
        """Test normalizing empty string returns None."""
        service = DateService()
        assert service.normalize_for_field("", "due_date") is None
        assert service.normalize_for_field("   ", "due_date") is None

    def test_normalize_datetime_passthrough(self):
        """Test datetime input is passed through unchanged."""
        service = DateService()
        dt = datetime(2025, 1, 15, 14, 30, 45)

        result = service.normalize_for_field(dt, "due_date")
        assert result == dt
        assert result is dt  # Should be same object

    def test_normalize_date_to_datetime_due_date(self):
        """Test date conversion for due_date field uses end of day."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        result = service.normalize_for_field(date_obj, "due_date")
        expected = datetime(2025, 1, 15, 23, 59, 59)
        assert result == expected

    def test_normalize_date_to_datetime_do_date(self):
        """Test date conversion for do_date field uses start of day."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        result = service.normalize_for_field(date_obj, "do_date")
        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected

    def test_normalize_date_to_datetime_unknown_field(self):
        """Test date conversion for unknown field uses start of day."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        result = service.normalize_for_field(date_obj, "unknown_field")
        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected

    def test_normalize_string_with_time(self):
        """Test string with time is parsed and time is preserved."""
        service = DateService()

        result = service.normalize_for_field("2025-01-15T14:30:45", "due_date")
        expected = datetime(2025, 1, 15, 14, 30, 45)
        assert result == expected

    def test_normalize_string_without_time_due_date(self):
        """Test string without time for due_date gets end of day."""
        service = DateService()

        result = service.normalize_for_field("2025-01-15", "due_date")
        expected = datetime(2025, 1, 15, 23, 59, 59)
        assert result == expected

    def test_normalize_string_without_time_do_date(self):
        """Test string without time for do_date gets start of day."""
        service = DateService()

        result = service.normalize_for_field("2025-01-15", "do_date")
        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected

    def test_normalize_string_without_time_completed_at(self):
        """Test string without time for completed_at gets current time."""
        service = DateService()

        with patch("app.src.domain.date_service.datetime") as mock_dt:
            mock_now = datetime(2025, 1, 15, 16, 45, 30)
            mock_dt.now.return_value = mock_now
            mock_dt.strptime.side_effect = datetime.strptime
            mock_dt.combine.side_effect = datetime.combine

            # Mock the parsed datetime from the string
            mock_parsed = datetime(2025, 1, 15, 0, 0, 0)

            # Test the semantic application directly
            result = service._apply_field_semantics(mock_parsed, "completed_at", False)
            expected = datetime(2025, 1, 15, 16, 45, 30)
            assert result == expected

    def test_normalize_invalid_type(self):
        """Test normalizing invalid type returns None."""
        service = DateService()
        assert service.normalize_for_field(123, "due_date") is None
        assert service.normalize_for_field([], "due_date") is None


class TestFieldSemantics:
    """Test field-specific semantic applications."""

    def test_apply_semantics_none_datetime(self):
        """Test applying semantics to None returns None."""
        service = DateService()
        result = service._apply_field_semantics(None, "due_date", False)
        assert result is None

    def test_apply_semantics_with_time_preserved(self):
        """Test datetime with time is preserved when has_time=True."""
        service = DateService()
        dt = datetime(2025, 1, 15, 14, 30, 45)

        result = service._apply_field_semantics(dt, "due_date", has_time=True)
        assert result == dt

    def test_apply_semantics_completed_at_current_time(self):
        """Test completed_at without time gets current time."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)

        with patch("app.src.domain.date_service.datetime") as mock_dt:
            mock_now = datetime(2025, 1, 15, 16, 45, 30)
            mock_dt.now.return_value = mock_now

            result = service._apply_field_semantics(dt, "completed_at", has_time=False)
            expected = datetime(2025, 1, 15, 16, 45, 30)
            assert result == expected

    def test_apply_semantics_due_date_end_of_day(self):
        """Test due_date without time gets end of day."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)

        result = service._apply_field_semantics(dt, "due_date", has_time=False)
        expected = datetime(2025, 1, 15, 23, 59, 59)
        assert result == expected

    def test_apply_semantics_do_date_start_of_day(self):
        """Test do_date without time gets start of day."""
        service = DateService()
        dt = datetime(2025, 1, 15, 12, 30, 45)

        result = service._apply_field_semantics(dt, "do_date", has_time=False)
        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected


class TestFieldTimeDefaults:
    """Test field time default lookup."""

    def test_get_field_time_due_date(self):
        """Test due_date returns end of day."""
        service = DateService()
        result = service._get_field_time("due_date")
        assert result == time(23, 59, 59)

    def test_get_field_time_do_date(self):
        """Test do_date returns start of day."""
        service = DateService()
        result = service._get_field_time("do_date")
        assert result == time(0, 0, 0)

    def test_get_field_time_unknown_field(self):
        """Test unknown field returns start of day."""
        service = DateService()
        result = service._get_field_time("unknown_field")
        assert result == time(0, 0, 0)


class TestDateToDatetime:
    """Test date to datetime conversion."""

    def test_date_to_datetime_due_date(self):
        """Test date conversion for due_date."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        result = service._date_to_datetime(date_obj, "due_date")
        expected = datetime(2025, 1, 15, 23, 59, 59)
        assert result == expected

    def test_date_to_datetime_do_date(self):
        """Test date conversion for do_date."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        result = service._date_to_datetime(date_obj, "do_date")
        expected = datetime(2025, 1, 15, 0, 0, 0)
        assert result == expected


class TestStorageFormatting:
    """Test formatting for storage."""

    def test_format_string_passthrough(self):
        """Test string input is passed through unchanged."""
        service = DateService()
        result = service.format_for_storage("2025-01-15", "due_date")
        assert result == "2025-01-15"

    def test_format_completed_at_full_timestamp(self):
        """Test completed_at always gets full timestamp."""
        service = DateService()
        dt = datetime(2025, 1, 15, 14, 30, 45)

        result = service.format_for_storage(dt, "completed_at")
        assert result == "2025-01-15T14:30:45"

    def test_format_date_only_semantics_due_date(self):
        """Test due_date with default time gets date-only format."""
        service = DateService()
        dt = datetime(2025, 1, 15, 23, 59, 59)  # Default time for due_date

        result = service.format_for_storage(dt, "due_date")
        assert result == "2025-01-15"

    def test_format_date_only_semantics_do_date(self):
        """Test do_date with default time gets date-only format."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)  # Default time for do_date

        result = service.format_for_storage(dt, "do_date")
        assert result == "2025-01-15"

    def test_format_custom_time_datetime_format(self):
        """Test datetime with custom time gets datetime format."""
        service = DateService()
        dt = datetime(2025, 1, 15, 14, 30, 0)  # Custom time

        result = service.format_for_storage(dt, "due_date")
        assert result == "2025-01-15T14:30"

    def test_format_unknown_field_with_default_time(self):
        """Test unknown field with default time gets date-only format."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)  # Default time

        result = service.format_for_storage(dt, "unknown_field")
        assert result == "2025-01-15"


class TestDateOnlySemantics:
    """Test date-only semantics detection."""

    def test_is_date_only_due_date_default_time(self):
        """Test due_date with default time is considered date-only."""
        service = DateService()
        dt = datetime(2025, 1, 15, 23, 59, 59)

        result = service._is_date_only_semantics(dt, "due_date")
        assert result is True

    def test_is_date_only_do_date_default_time(self):
        """Test do_date with default time is considered date-only."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)

        result = service._is_date_only_semantics(dt, "do_date")
        assert result is True

    def test_is_not_date_only_custom_time(self):
        """Test datetime with custom time is not considered date-only."""
        service = DateService()
        dt = datetime(2025, 1, 15, 14, 30, 45)

        result = service._is_date_only_semantics(dt, "due_date")
        assert result is False

    def test_is_not_date_only_wrong_default_time(self):
        """Test datetime with wrong default time is not considered date-only."""
        service = DateService()
        dt = datetime(2025, 1, 15, 0, 0, 0)  # do_date default time

        result = service._is_date_only_semantics(dt, "due_date")
        assert result is False


class TestUtilityFunctions:
    """Test utility functions and singleton pattern."""

    def test_now_timestamp_str_format(self):
        """Test current timestamp formatting."""
        with patch("app.src.domain.date_service.datetime") as mock_dt:
            mock_now = datetime(2025, 1, 15, 14, 30, 45)
            mock_dt.now.return_value = mock_now

            result = DateService.now_timestamp_str()
            assert result == "2025-01-15T14:30:45"

    def test_get_date_service_singleton(self):
        """Test singleton pattern returns same instance."""
        service1 = get_date_service()
        service2 = get_date_service()

        assert service1 is service2
        assert isinstance(service1, DateService)

    def test_normalize_date_field_convenience(self):
        """Test convenience function delegates to service."""
        result = normalize_date_field("2025-01-15", "due_date")
        expected = datetime(2025, 1, 15, 23, 59, 59)
        assert result == expected

    def test_parse_date_string_convenience(self):
        """Test convenience function delegates to service."""
        result = parse_date_string("2025-01-15T14:30:45")
        expected = datetime(2025, 1, 15, 14, 30, 45)
        assert result == expected


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_leap_year_parsing(self):
        """Test leap year date parsing."""
        service = DateService()
        result = service.parse_date_string("2024-02-29")
        expected = datetime(2024, 2, 29, 0, 0, 0)
        assert result == expected

    def test_year_boundaries(self):
        """Test year boundary dates."""
        service = DateService()

        # Test minimum reasonable year
        result1 = service.parse_date_string("1900-01-01")
        assert result1 == datetime(1900, 1, 1, 0, 0, 0)

        # Test maximum reasonable year
        result2 = service.parse_date_string("2099-12-31")
        assert result2 == datetime(2099, 12, 31, 0, 0, 0)

    def test_midnight_and_endofday_precision(self):
        """Test precise time handling for field defaults."""
        service = DateService()

        # Test start of day precision
        dt_start = datetime(2025, 1, 15, 0, 0, 0)
        assert service._is_date_only_semantics(dt_start, "do_date") is True

        # Test end of day precision
        dt_end = datetime(2025, 1, 15, 23, 59, 59)
        assert service._is_date_only_semantics(dt_end, "due_date") is True

        # Test one second off
        dt_off = datetime(2025, 1, 15, 23, 59, 58)
        assert service._is_date_only_semantics(dt_off, "due_date") is False

    def test_whitespace_handling(self):
        """Test various whitespace scenarios."""
        service = DateService()

        # Leading/trailing whitespace should be handled
        assert service.parse_date_string("  ") is None
        assert service.parse_date_string("\t\n") is None
        assert service.parse_date_string("") is None

    def test_field_name_case_sensitivity(self):
        """Test field name handling is case sensitive."""
        service = DateService()
        date_obj = date(2025, 1, 15)

        # Should use start of day for unknown case variations
        result = service.normalize_for_field(date_obj, "DUE_DATE")
        expected = datetime(2025, 1, 15, 0, 0, 0)  # Default, not end of day
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
