import re
import pytz
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict

def convert_iso_to_erpnext_datetime(iso_datetime: str, user_time_zone: str) -> str:
    """
    Convert an ISO 8601 datetime string into an ERPNext compatible datetime format (YYYY-MM-DD HH:MM:SS), and sets time to local timezone (time is fetch in UTC).

    Args:
        iso_datetime (str): The ISO 8601 datetime string ('2025-01-01T10:00:00Z)
        user_time_zone (str): Time zone of user from clockify (Europ/Zurich)

    Returns:
        str: A string in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    iso_cleaned = iso_datetime.replace("Z", "")

    dt_naive_utc = datetime.strptime(iso_cleaned, "%Y-%m-%dT%H:%M:%S")

    dt_utc = pytz.utc.localize(dt_naive_utc)
    local_tz = pytz.timezone(user_time_zone)

    local_dt = dt_utc.astimezone(local_tz)

    return local_dt.strftime("%Y-%m-%d %H:%M:%S")

def convert_erpnext_to_iso_datetime(erpnext_datetime: str) -> str:
    """
    Convert ERPNext datetime format to a ISO 8601 datetime string (YYYY-MM-DDTHH:MM:SSZ).

    Args:
        erpnext_datetime: The ERPNext datetime string ('2025-01-01 10:00:00)

    Returns:
        str: A string in the ISO 8601 format
    """
    datetime_obj = datetime.strptime(erpnext_datetime, "%Y-%m-%d %H:%M:%S")
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_duration(duration: str) -> Tuple[float, str]:
    """
    Parse an ISO 8601 duration string (PT1H30M) and returns the total hours in decimal plus a 'HH:MM' string.

    Args:
        duration (str): ISO 8601 formatted duration
    
    Returns:
        Tuple[float, str]: hours_in_decimal (1.5), formatted string (HH:MM).
    
    Raises:
        ValueError: If the string doesn't match an expected ISO 8601 pattern.
    """
    hours, minutes = 0, 0
    match = re.match(r"PT((\d+)H)?((\d+)M)?", duration)
    if not match:
        raise ValueError(f"Ungültiges ISO-8601-Dauerformat: {duration}")
    
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))

    return hours + (minutes / 60), f"{hours}:{minutes:02}"

def parse_hhmm_to_minutes(hhmm: str) -> int:
    """
    Converts a 'HH:MM' string into total minutes (int).

    Args:
        hhmm (str): The time string
    
    Returns:
        int: Total minutes (2:05 -> 125).
    """
    hours_str, minutes_str = hhmm.split(":")
    return int(hours_str) * 60 + int(minutes_str)

def round_minutes_to_5(total_minutes: int) -> int:
    """
    Round the given minutes to the nearest 5-minute block.

    Args:
        total_minutes (int): The original number of minutes.

    Returns:
        int: The minutes, rounded to the nearest multiple of 5.
    """
    return int(round(total_minutes / 5.0)) * 5

def minutes_to_hhmm(total_minutes: int) -> str:
    """
    Convert total minutes into an 'HH:MM' string.

    Args:
        total_minutes (int): Total minutes (130)

    Returns:
        str: 'HH:MM' format (2:10)
    """
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

def build_html_link(url: str, text: str) -> str:
    """
    Build a clickable HTML link string with basic styling.

    Args:
        url (str): The hyperlink URL.
        text (str): The link text to be displayed.

    Returns:
        str: A simple HTML <a> tag with the provided URL an text.
    """
    return f"""
    <a href="{url}"
    target="_blank" 
    style="color: #007bff; text-decoration: underline; font-weight: bold;">
    {text}
    </a>
"""