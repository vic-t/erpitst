import frappe
import requests
import re
from datetime import datetime

CLOCKIFY_API_KEY = "api_key"
WORKSPACE_ID = "workspace_id"
CLOCKIFY_BASE_URL = "https://api.clockify.me/api/v1"

def fetch_clockify_entry(entry_id):
    url = f"{CLOCKIFY_BASE_URL}/workspaces/{WORKSPACE_ID}/time-entries/{entry_id}"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch entry: {response.status_code}, {response.text}")


def convert_iso_to_erpnext_datetime(iso_datetime):
    dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    erpnext_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
    return erpnext_datetime

def parse_duration(duration):
    hours = 0
    minutes = 0
    match = re.match(r"PT((\d+)H)?((\d+)M)?", duration)
    if not match:
        frappe.throw(f"Invalid duration format: {duration}")
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))
    return hours + (minutes / 60), f"{hours}:{minutes:02}"

def create_timesheet_with_initial_log(company, employee, time_log_data):
    try:
        print("Time Log Data (before insert):", time_log_data)
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "company": company,
            "employee": employee,
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    **time_log_data,
                }
            ],
        })    
        
        print("Timesheet Data Before Insert:", timesheet.as_dict())

        timesheet.insert()
        print("Timesheet Data After Insert:", timesheet.as_dict())

        frappe.db.commit()
        print("Timesheet Inserted Successfully:", timesheet.name)

        return timesheet.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Timesheet Error")

def add_time_log_to_timesheet(timesheet_name, time_log_data):
    try:
        timesheet = frappe.get_doc("Timesheet", timesheet_name)

        for log in timesheet.time_logs:
            log.from_time = str(log.from_time)
            log.to_time = str(log.to_time)
        
        timesheet.append("time_logs", {
            #"doctype": "Timesheet Detail",
            **time_log_data,
        })
        print("Timesheet Data Before Insert:", timesheet.as_dict())

        timesheet.save()

        print("Timesheet Data After Insert:", timesheet.as_dict())

        frappe.db.commit()
        return timesheet.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Time Log to Timesheet Error")

def import_clockify_entry_to_timesheet(entry_id=None):
    try:
        clockify_entry = fetch_clockify_entry(entry_id)
        from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
        to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])
        duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

        billing_rate = clockify_entry["hourlyRate"]["amount"]
        billing_rate /= 100
        print(f"Billing rate: {billing_rate}")

        billing_amount = billing_rate * duration_hours
        print(f"Billing amount: {billing_amount}")

        time_log_data = {
            "activity_type": "Planung",
            "from_time": from_time,
            "to_time": to_time,
            "duration": duration_formatted,
            "hours": duration_hours,
            "project": "test",
            "billable": clockify_entry["billable"],
            "billing_duration": duration_formatted,
            "billing_hours": duration_hours,
            "billing_rate": billing_rate,
            "billing_amount": billing_amount,
            "category": "test-001",
            "remarks": clockify_entry.get("description", "Default Remarks"),
        }

        print("Time Log Data:", time_log_data)

        company = "ITST"
        employee = "HR-EMP-00001"
        #timesheet_name = create_timesheet_with_initial_log(company, employee, time_log_data)

        timesheet_name = "TS-2024-00030"

        if timesheet_name:
            add_time_log_to_timesheet(timesheet_name, time_log_data)
            frappe.msgprint(f"Clockify entry added to Timesheet {timesheet_name} successfully.")
        else:
            frappe.throw("Timesheet not found. Cannot add log.")

        frappe.msgprint(f"Clockify entry imported into Timesheet {timesheet_name} successfully.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Clockify Import Error")
