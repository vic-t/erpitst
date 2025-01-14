import re
from datetime import datetime, timezone, timedelta

def convert_iso_to_erpnext_datetime(iso_datetime):
    #get timezone dynamically, not hardcoded, get timezone via config or parameter
    datetime_obj = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    datetime_obj = datetime_obj.astimezone(timezone(timedelta(hours=1)))
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

def parse_duration(duration):
    hours, minutes = 0, 0
    match = re.match(r"PT((\d+)H)?((\d+)M)?", duration)
    if not match:
        raise ValueError(f"Ungültiges ISO-8601-Dauerformat: {duration}")
    
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))

    return hours + (minutes / 60), f"{hours}:{minutes:02}"

def parse_hhmm_to_minutes(hhmm):
    hours_str, minutes_str = hhmm.split(":")
    return int(hours_str) * 60 + int(minutes_str)

def round_minutes_to_5(total_minutes):
    return int(round(total_minutes / 5.0)) * 5

def minutes_to_hhmm(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

def build_html_link(url,text):
    return f"""
    <a href="{url}"
    target="_blank" 
    style="color: #007bff; text-decoration: underline; font-weight: bold;">
    {text}
    </a>
"""

def get_week_start_iso():
    today = datetime.utcnow().date()
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    return f"{monday.isoformat()}T00:00:00Z"