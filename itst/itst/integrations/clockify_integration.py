import frappe
import requests
import re
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


load_dotenv()

CLOCKIFY_API_KEY = os.getenv("CLOCKIFY_API_KEY")
CLOCKIFY_BASE_URL = "https://api.clockify.me/api/v1"


def fetch_all_clockify_entries(workspace_id, clockify_user_id):
    get_week_before = get_import_time()
    url = f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/user/{clockify_user_id}/time-entries"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY}

    start = "2024-12-19T00:00:00Z"
    end = "2024-12-20T00:00:00Z"

    params = {
        "get-week-before": get_week_before,
        #"start": start,  
        #"end": end,      
        "hydrated": "true",
        "page": 1,
        "page-size": 5000
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        entries = response.json()
        return entries
    else:
        frappe.log_error(f"Fehler beim Abrufen der Einträge.: {response.status_code}, {response.text}")
        frappe.throw("Fehler beim Abrufen der Einträge.")

def convert_iso_to_erpnext_datetime(iso_datetime):
    dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    dt = dt.astimezone(timezone(timedelta(hours=1)))
    erpnext_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
    print(erpnext_datetime)
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


def create_timesheet(company, erpnext_employee_id, time_log_data, unique_Timesheet_name):
    timesheet = frappe.get_doc({
        "doctype": "Timesheet",
        "company": company,
        "employee": erpnext_employee_id,
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

def process_single_clockify_entry(clockify_entry, erpnext_employee_id, erpnext_employee_name):
    from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
    to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])

    duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

    project_name = clockify_entry["project"]["name"]
    entry_id = clockify_entry["id"]

    unique_Timesheet_name = f"{erpnext_employee_name}_{project_name}"
    timesheet_name = find_or_create_timesheet(unique_Timesheet_name)

    billing_rate = clockify_entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * duration_hours

    company = "ITST"
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
        "category": "test-001 ",
        "remarks": clockify_entry.get("description", "Default Remarks"),
        "clockify_entry_id": entry_id
    }

    if timesheet_name:
        add_time_log_to_timesheet(timesheet_name, time_log_data)
    else:
        new_timesheet_name = create_timesheet(company, erpnext_employee_id, time_log_data, unique_Timesheet_name)
        timesheet_name = new_timesheet_name

    workspace_id = clockify_entry["workspaceId"] 
    update_clockify_entry(workspace_id, clockify_entry)

    return timesheet_name

def import_clockify_entries_to_timesheet(workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name):
    entries = fetch_all_clockify_entries(workspace_id, clockify_user_id)

    if not entries:
        frappe.msgprint("Keine Einträge gefunden.")
        return
    
    missing_projects = set()
    imported_count = 0
    error_count = 0
    errors = []
    for entry in entries:
        project_name = entry["project"]["name"]
        try:
            if not project_validation(project_name):
                if project_name not in missing_projects:
                    missing_projects.add(project_name)
                    frappe.throw(f"Das im Eintrag angegebene Projekt '{project_name}' existiert nicht in ERPNext. Bitte legen Sie das Projekt zuerst an oder korrigieren Sie den Projektnamen im Clockify-Eintrag.") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple
                else:
                    raise Exception(f"Projekt '{project_name}' fehlt weiterhin.")
            
            duplicate_imports_validation(entry["id"])
            result = process_single_clockify_entry(entry, erpnext_employee_id, erpnext_employee_name)
            if result is not None:
                imported_count += 1
        except Exception as e:

            frappe.log_error(frappe.get_traceback(), f"Fehler bei der Verarbeitung des Clockify-Eintrags. {entry.get('id')}") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple
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
        frappe.throw("Ausgewählter user nicht gefunden. Bitte Import nochmals versuchen")
    
    clockify_user_id = selected_mapping.clockify_user_id
    erpnext_employee_id = selected_mapping.erpnext_employee
    erpnext_employee_name = selected_mapping.erpnext_employee_name

    import_clockify_entries_to_timesheet(workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name) 

def project_validation(project_name):
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        return False
    return True 

def duplicate_imports_validation(entry_id):
    if frappe.db.exists("Timesheet Detail", {"clockify_entry_id": entry_id}):
        frappe.throw(f"Eintrag \"{entry_id}\" wurden bereits importiert") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple


def update_clockify_entry(workspace_id, entry):
    url = f"{CLOCKIFY_BASE_URL}/workspaces/{workspace_id}/time-entries/{entry['id']}"
    headers = {"X-Api-Key": CLOCKIFY_API_KEY, "Content-Type": "application/json"}

    data = {
        "description": entry.get("description", "No description"),
        "end": entry["timeInterval"]["end"],
        "projectId": entry["projectId"],
        "start": entry["timeInterval"]["start"],
        "tagIds": ["675c4ba16f79f63af4d20203"],
    }

    response = requests.put(url, headers=headers, json=data)
    if response.status_code != 200:
        frappe.log_error(f"Clockify-Eintrag {entry['id']} konnte nach dem Import nicht aktualisiert werden: {response.status_code}, {response.text}“, “Clockify Update Fehler")


def get_import_time():
    today = datetime.utcnow().date()

    weekday = today.weekday()

    monday = today - timedelta(days=weekday)

    get_week_before = f"{monday.isoformat()}T00:00:00Z"

    return get_week_before
