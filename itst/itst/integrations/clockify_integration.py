import frappe
import requests
import re
import time
import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
WORKSPACE_ID = os.getenv("CLOCKIFY_WORKSPACE_ID")
CLOCKIFY_BASE_URL = "https://api.clockify.me/api/v1"
USER_ID = os.getenv("USER_ID")


def fetch_all_clockify_entries(workspace_id, clockify_user_id):
    url = f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/user/{clockify_user_id}/time-entries"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}

    start = "2024-12-13T00:00:00Z"
    end = "2024-12-14T00:00:00Z"

    params = {
        "start": start,  
        "end": end,      
        "hydrated": "true", 
    }

    all_entries = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            frappe.log_error(f"Failed to fetch entries: {response.status_code}, {response.text}")
            break

        entries = response.json()

        if not entries:
            # no more entries
            print(f"all entries {all_entries}")
            break

        all_entries.extend(entries)

        params["page"] += 1

    return all_entries

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

def create_timesheet(company, employee, time_log_data, unique_Timesheet_name):
    try:
        print("Time Log Data (before insert):", time_log_data)
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "company": company,
            "employee": employee,
            "title": unique_Timesheet_name,
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
            "doctype": "Timesheet Detail",
            **time_log_data,
        })
        print("Timesheet Data Before Insert:", timesheet.as_dict())

        timesheet.save()

        print("Timesheet Data After Insert:", timesheet.as_dict())

        frappe.db.commit()
        return timesheet.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Time Log to Timesheet Error")

def find_or_create_timesheet(unique_Timesheet_name):
    print(f"Timesheet name: {unique_Timesheet_name}")
    timesheets = frappe.get_list(
        "Timesheet",
        filters={
            "title": unique_Timesheet_name,
            "status": "Draft"
            },  # Filtering by title and Draft documents
        fields=["name"]
    )
    print(f"Timesheet found: {timesheets}")
    return timesheets[0].name if timesheets else None

def process_single_clockify_entry(clockify_entry):
    try:
        from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
        to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])

        duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

        project_name = clockify_entry["project"]["name"]
        user_name = clockify_entry["user"]["name"]

        billing_rate = clockify_entry["hourlyRate"]["amount"] / 100
        billing_amount = billing_rate * duration_hours

        time_log_data = {
            "activity_type": "Planung",
            "from_time": from_time,
            "to_time": to_time,
            "duration": duration_formatted,
            "hours": duration_hours,
            "project": project_name,
            "billable": clockify_entry["billable"],
            "billing_duration": duration_formatted,
            "billing_hours": duration_hours,
            "billing_rate": billing_rate,
            "billing_amount": billing_amount,
            "category": "test-001",
            "remarks": clockify_entry.get("description", "Default Remarks"),
        }

        company = "ITST"
        employee = "HR-EMP-00001"

        unique_Timesheet_name = f"{user_name}_{project_name}"

        timesheet_name = find_or_create_timesheet(unique_Timesheet_name)

        if timesheet_name:
            add_time_log_to_timesheet(timesheet_name, time_log_data)
        else:
            new_timesheet_name = create_timesheet(company, employee, time_log_data, unique_Timesheet_name)
            timesheet_name = new_timesheet_name

        return timesheet_name

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Clockify Import Error")

def import_clockify_entries_to_timesheet(workspace_id, clockify_user_id):
    try:
        all_entries = fetch_all_clockify_entries(workspace_id, clockify_user_id)

        if not all_entries:
            frappe.msgprint("No new entries found.")
            return

        imported_count = 0
        for entry in all_entries:
            process_single_clockify_entry(entry)
            imported_count += 1

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Clockify Multi Import Error")


@frappe.whitelist()
def run_clockify_import():
    settings = frappe.get_doc("Clockify Import Settings")
    workspace_id = settings.workspace_id

    for mapping in settings.user_mappings:
        clockify_user_id = mapping.clockify_user_id
    print("clockify user id:", clockify_user_id)
    print(f"workspace {workspace_id}")

    import_clockify_entries_to_timesheet(workspace_id, clockify_user_id)