import frappe
import requests
import re
import os
from dotenv import load_dotenv
from datetime import datetime,timezone,timedelta


load_dotenv()

CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
WORKSPACE_ID = os.getenv("CLOCKIFY_WORKSPACE_ID")
CLOCKIFY_BASE_URL = "https://api.clockify.me/api/v1"
USER_ID = os.getenv("USER_ID")

def fetch_all_clockify_entries(workspace_id, clockify_user_id):
    url = f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/user/{clockify_user_id}/time-entries"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}

    start = "2024-12-19T00:00:00Z"
    end = "2024-12-20T00:00:00Z"

    params = {
        "start": start,  
        "end": end,      
        "hydrated": "true",
        "page": 1,
        "page-size": 50
    }

    all_entries = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            frappe.log_error(f"Fehler beim Abrufen der Einträge.: {response.status_code}, {response.text}")
            frappe.throw("Fehler beim Abrufen der Einträge.")
            break

        entries = response.json()

        if not entries:
            # no more entries
            break

        all_entries.extend(entries)

        params["page"] += 1

    return all_entries

def convert_iso_to_erpnext_datetime(iso_datetime):
    dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    dt = dt.astimezone(timezone(timedelta(hours=1)))
    erpnext_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
    return erpnext_datetime

def parse_duration(duration):
    hours = 0
    minutes = 0
    match = re.match(r"PT((\d+)H)?((\d+)M)?", duration)
    if not match:
        frappe.throw(f"Ungültiges Dauerformat: {duration}")
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))
    return hours + (minutes / 60), f"{hours}:{minutes:02}"

def create_timesheet(company, employee, time_log_data, unique_Timesheet_name):

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
    
    timesheet.insert()
    frappe.db.commit()
    return timesheet.name

def add_time_log_to_timesheet(timesheet_name, time_log_data):
    timesheet = frappe.get_doc("Timesheet", timesheet_name)

    for log in timesheet.time_logs:
        log.from_time = str(log.from_time)
        log.to_time = str(log.to_time)
    
    timesheet.append("time_logs", {
        "doctype": "Timesheet Detail",
        **time_log_data,
    })
    timesheet.save()
    frappe.db.commit()
    return timesheet.name

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
    return timesheets[0].name if timesheets else None

def process_single_clockify_entry(clockify_entry, employee):
    from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
    to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])

    duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

    project_name = clockify_entry["project"]["name"]
    user_name = clockify_entry["user"]["name"]

    unique_Timesheet_name = f"{user_name}_{project_name}"
    timesheet_name = find_or_create_timesheet(unique_Timesheet_name)

    billing_rate = clockify_entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * duration_hours

    company = "ITST"
    time_log_data = {
        "activity_type": "Planning",
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
        "category": "Elia ",
        "remarks": clockify_entry.get("description", "Default Remarks"),
    }

    if timesheet_name:
        add_time_log_to_timesheet(timesheet_name, time_log_data)
    else:
        new_timesheet_name = create_timesheet(company, employee, time_log_data, unique_Timesheet_name)
        timesheet_name = new_timesheet_name

    return timesheet_name

def import_clockify_entries_to_timesheet(workspace_id, clockify_user_id, employee):
    all_entries = fetch_all_clockify_entries(workspace_id, clockify_user_id)

    if not all_entries:
        frappe.msgprint("Keine Einträge gefunden.")
        return

    imported_count = 0
    error_count = 0
    errors = []
    for entry in all_entries:
        try:

            result = None
            if project_validation(entry["project"]["name"]):
                result = process_single_clockify_entry(entry, employee)
            if result is not None:
                imported_count += 1
        except Exception as e:

            frappe.log_error(frappe.get_traceback(), f"Fehler bei der Verarbeitung des Clockify-Eintrags. {entry.get('id')}")
            error_count += 1

            errors.append(f"Eintrag {entry.get('id')}: {str(e)}")

    frappe.db.commit() 
    
    if error_count > 0:
        frappe.throw(f"{imported_count} Einträge erfolgreich importiert, aber {error_count} Einträge sind fehlgeschlagen. Siehe Error log für Details.")
    else:
        frappe.msgprint(f"{imported_count} Einträge erfolgreich importiert.")

@frappe.whitelist()
def run_clockify_import(user_mapping_name):
    settings = frappe.get_doc("Clockify Import Settings")
    workspace_id = settings.workspace_id

    selected_mapping = None
    for m in settings.user_mapping:
        if m.erpnext_employee == user_mapping_name:
            selected_mapping = m
            break
    
    if not selected_mapping:
        frappe.throw("Ausgewählter user nicht gefunden.")
    
    clockify_user_id = selected_mapping.clockify_user_id
    erpnext_employee = selected_mapping.erpnext_employee

    import_clockify_entries_to_timesheet(workspace_id, clockify_user_id, erpnext_employee) 

def project_validation(project_name):
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        frappe.msgprint(
            msg=f"Project {project_name} does not exist.",
            title="Error",
            indicator="red"
        )
        frappe.throw(f"Project '{project_name}' does not exist. Please correct the name.")
    return True