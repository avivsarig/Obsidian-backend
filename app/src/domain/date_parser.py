from datetime import datetime


class TimeParserMixin:
    def parse_str(self, date_str: str):
        if date_str == "":
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Invalid date format: {date_str}")
