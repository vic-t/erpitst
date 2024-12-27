import frappe
import requests
import re
from datetime import datetime, timezone, timedelta


def fetch_clockify_entries(workspace_id, clockify_user_id, clockify_api_key, clockify_base_url):
    get_week_before = get_import_time()
    url = f"{clockify_base_url}/workspaces/{workspace_id}/user/{clockify_user_id}/time-entries"
    headers = {"X-Api-Key": clockify_api_key}

    start = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")
    end = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    
    params = {
        #"get-week-before": get_week_before,   
        "hydrated": "true",
        "page": 1,
        "page-size": 5000,
        "start":start,
        "end":end
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        entries = response.json()
        return entries
    else:
        frappe.log_error(f"Fehler beim Abrufen der Einträge: {response.status_code}, {response.text}. Bitte überprüfen Sie Ihre API-Schlüssel und die Anfrageparameter.")
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
        frappe.throw(f"Das Format der angegebenen Dauer ist ungültig: {duration}.Bitte stellen Sie sicher, dass die Dauer im ISO 8601-Format (z. B. 'PT1H30M') angegeben ist.")
    if match.group(2):  # Hours
        hours = int(match.group(2))
    if match.group(4):  # Minutes
        minutes = int(match.group(4))
    return hours + (minutes / 60), f"{hours}:{minutes:02}"


def create_erpnext_timesheet(company, erpnext_employee_id, time_log_data, unique_Timesheet_name):
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
    #frappe.db.commit()
    return timesheet.name

def add_detail_to_timesheet (timesheet_name, time_log_data):
    timesheet = frappe.get_doc("Timesheet", timesheet_name)

    for log in timesheet.time_logs:
        log.from_time = str(log.from_time)
        log.to_time = str(log.to_time)
    
    timesheet.append("time_logs", {
        "doctype": "Timesheet Detail",
        **time_log_data,
    })
    timesheet.save()
    #frappe.db.commit()
    return timesheet.name

def find_timesheet(unique_Timesheet_name):
    timesheets = frappe.get_list(
        "Timesheet",
        filters={
            "title": unique_Timesheet_name,
            "status": "Draft"
            },  # Filtering by title and Draft documents
        fields=["name"]
    )
    return timesheets[0].name if timesheets else None

def process_clockify_entry_to_erpnext(clockify_entry, erpnext_employee_id, erpnext_employee_name, clockify_tagsid, clockify_api_key, clockify_base_url):
    from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
    to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])

    duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

    project_name = clockify_entry["project"]["name"]
    entry_id = clockify_entry["id"]

    unique_Timesheet_name = f"{erpnext_employee_name}_{project_name}"
    timesheet_name = find_timesheet(unique_Timesheet_name)

    billing_rate = clockify_entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * duration_hours

    company = "ITST"
    time_log_data = {
        "activity_type": "Research",
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
        "category": "Elia",
        "remarks": clockify_entry.get("description", "Default Remarks"),
        "clockify_entry_id": entry_id
    }

    workspace_id = clockify_entry["workspaceId"] 
    update_clockify_entry(workspace_id, clockify_entry, clockify_tagsid, clockify_api_key, clockify_base_url)

    if timesheet_name:
        add_detail_to_timesheet (timesheet_name, time_log_data)
    else:
        new_timesheet_name = create_erpnext_timesheet(company, erpnext_employee_id, time_log_data, unique_Timesheet_name)
        timesheet_name = new_timesheet_name

    return timesheet_name

def build_html_link(url,text):
    return f"""
    <a href="{url}"
    target="_blank" 
    style="color: #007bff; text-decoration: underline; font-weight: bold;">
    {text}
    </a>
"""
def import_clockify_entries (workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name, clockify_api_key, clockify_base_url, clockify_tagsid):
    entries = fetch_clockify_entries(workspace_id, clockify_user_id, clockify_api_key, clockify_base_url)
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
            if not validate_project_existence (project_name):
                if project_name not in missing_projects:
                    missing_projects.add(project_name)
                    link_create_project = build_html_link("http://erp.itst.ch.localhost:8000/desk#Form/Project/New%20Project%201", "Neues Projekt erstellen")
                    frappe.throw(f"Das im Eintrag angegebene Projekt '{project_name}' existiert nicht in ERPNext. Bitte legen Sie das Projekt zuerst an oder korrigieren Sie den Projektnamen im Clockify-Eintrag.{link_create_project}") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple
                else:
                    raise Exception(f"Projekt '{project_name}' fehlt weiterhin.")
            
            check_for_duplicate_import(entry["id"])
            result = process_clockify_entry_to_erpnext(entry, erpnext_employee_id, erpnext_employee_name, clockify_tagsid, clockify_api_key, clockify_base_url)
            if result is not None:
                imported_count += 1
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Fehler bei der Verarbeitung des Clockify-Eintrags. {entry.get('id')}") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple
            error_count += 1
            errors.append(f"Eintrag {entry.get('id')}: {str(e)}")

    frappe.db.commit() 
    if error_count > 0:
        link_error_log = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Error%20Log/List", "Error log")
        frappe.throw(f"Der Importprozess wurde abgeschlossen: {imported_count} Einträge wurden erfolgreich importiert. Allerdings {error_count} Einträge sind fehlgeschlagen. Bitte überprufen Sie die Fehlerdetails unter {link_error_log}.")
    else:
        link_timesheet = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Timesheet/List", "Timesheet")
        frappe.msgprint(f"Der Importprozess wurde erfolgreich abgeschlossen: Ingesamt wurden {imported_count} Einträge erfolgreich importiert. Sie können die importierten Daten jetzt im Timesheet-Bereich einsehen, indem Sie den folgenden Link verwenden {link_timesheet}.")

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
    clockify_api_key = settings.get_password('api_key')
    clockify_base_url = settings.clockify_url
    clockify_tagsid = settings.tags_id

    import_clockify_entries (workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name, clockify_api_key, clockify_base_url, clockify_tagsid)

def validate_project_existence (project_name):
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        return False
    return True 

def check_for_duplicate_import(entry_id):
    if frappe.db.exists("Timesheet Detail", {"clockify_entry_id": entry_id}):
        frappe.throw(f"Der Eintrag mit der ID \"{entry_id}\" wurde bereits importiert. Doppelte Importe sind nicht erlaubt. Überprüfen sie die vorhandenen Einträge im Timesheet.") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple


def update_clockify_entry(workspace_id, entry, clockify_tagsid, clockify_api_key, clockify_base_url):
    url = f"{clockify_base_url}/workspaces/{workspace_id}/time-entries/{entry['id']}"
    headers = {"X-Api-Key": clockify_api_key, "Content-Type": "application/json"}

    data = {
        "description": entry.get("description", "No description"),
        "end": entry["timeInterval"]["end"],
        "projectId": entry["projectId"],
        "start": entry["timeInterval"]["start"],
        "tagIds": [f"{clockify_tagsid}"],
    }

    response = requests.put(url, headers=headers, json=data)
    if response.status_code != 200:
        frappe.log_error(f"Fehler beim Aktualisieren des Clockify-Eintrags nach dem Import: Die Aktualisierung des Eintrags mit der ID {entry['id']} ist fehlgeschlagen. HTTP-Statuscode: {response.status_code}, Serverantwort: {response.text}. Bitte überprüfen Sie die API-Schlüssel, den Eintrag oder die Verbindung zu Clockify.", "Clockify Update Fehler")
        frappe.throw(f" Der Clockify-Eintrag mit der ID {entry['id']} konnte nach dem Import nicht aktualisiert werden. Dies könnte auf einen API-Fehler oder ein Problem mit der Verbindung zu Clockify hinweisen. Bitte wenden Sie sich an den Administrator, um den Fehler zu beheben.")


def get_import_time():
    today = datetime.utcnow().date()
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    get_week_before = f"{monday.isoformat()}T00:00:00Z"

    return get_week_before
