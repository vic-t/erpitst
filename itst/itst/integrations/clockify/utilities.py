import re
from datetime import datetime, timezone, timedelta

def convert_iso_to_erpnext_datetime(iso_datetime):
    datetime_obj = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    #get timezone dynamically, not hardcoded, get timezone via config or parameter
    datetime_obj = datetime_obj.astimezone(timezone(timedelta(hours=1)))
    erpnext_datetime = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    return erpnext_datetime

def parse_duration(duration):
    hours = 0
    minutes = 0
    match = re.match(r"PT((\d+)H)?((\d+)M)?", duration)
    if not match:
        raise ValueError(f"Ungültiges ISO-8601-Dauerformat: {duration}")
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))
    return hours + (minutes / 60), f"{hours}:{minutes:02}"

def get_week_start_iso():
    today = datetime.utcnow().date()
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    week_start_iso = f"{monday.isoformat()}T00:00:00Z"
    return week_start_iso

def parse_hhmm_to_minutes(hhmm):
    hours_str, minutes_str = hhmm.split(":") 
    hours = int(hours_str)
    minutes = int(minutes_str)
    total_minutes = hours * 60 + minutes
    return total_minutes

def round_minutes_to_5(total_minutes):
    quotient = total_minutes / 5.0
    rounded = int(quotient + 0.5)
    return rounded * 5

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