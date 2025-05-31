#utils/date_utils.py

from datetime import datetime

def parse_date(date_str: str) -> str:
    """Parse date string to RFC3339 format"""
    try:
        # Handle full ISO8601 format
        if 'T' in date_str:
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed.isoformat(timespec='seconds').replace('+00:00', 'Z')
        # Handle date-only format
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed.isoformat(timespec='seconds').replace('+00:00', 'Z')
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ") from e
