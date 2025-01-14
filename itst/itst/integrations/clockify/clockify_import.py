import frappe
from datetime import datetime, timedelta

from .clockify_service import fetch_clockify_entries, update_clockify_entry
from .erpnext_timesheet_service import (
    create_erpnext_timesheet,
    add_detail_to_timesheet,
    find_timesheet
)
from .utilities import (
    convert_iso_to_erpnext_datetime,
    parse_duration,
    parse_hhmm_to_minutes,
    round_minutes_to_5,
    minutes_to_hhmm,
    build_html_link,
)

def process_clockify_entry_to_erpnext(clockify_entry, erpnext_employee_id, erpnext_employee_name, clockify_tags_id, clockify_api_key, clockify_base_url, dienstleistungs_artikel, activity_type):
    from_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["start"])
    to_time = convert_iso_to_erpnext_datetime(clockify_entry["timeInterval"]["end"])
    duration_hours, duration_formatted = parse_duration(clockify_entry["timeInterval"]["duration"])

    duration_in_minutes = parse_hhmm_to_minutes(duration_formatted)
    duration_rounded_in_minutes = round_minutes_to_5(duration_in_minutes)
    duration_rounded_hhmm = minutes_to_hhmm(duration_rounded_in_minutes)

    datetime_format = "%Y-%m-%d %H:%M:%S"
    from_time_dt = datetime.strptime(from_time, datetime_format)
    to_time_dt = from_time_dt + timedelta(minutes=duration_rounded_in_minutes)
    to_time_str = to_time_dt.strftime(datetime_format)
    
    project_name = clockify_entry["project"]["name"]
    entry_id = clockify_entry["id"]
    timesheet_title  = f"{erpnext_employee_name}_{project_name}"
    timesheet_name = find_timesheet(timesheet_title )
    billing_rate = clockify_entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * duration_hours

    company = "ITST"
    timesheet_detail_data = {
        "activity_type": activity_type,
        "from_time": from_time,
        "to_time": to_time_str,
        "duration": duration_rounded_hhmm,
        "hours": duration_hours,
        "project": project_name,
        "billable": clockify_entry["billable"],
        "billing_duration": duration_rounded_hhmm,
        "billing_hours": duration_hours,
        "billing_rate": billing_rate,
        "billing_amount": billing_amount,
        "category": dienstleistungs_artikel,
        "remarks": clockify_entry.get("description", "Default Remarks"),
        "clockify_entry_id": entry_id
    }
    workspace_id = clockify_entry["workspaceId"] 
    update_clockify_entry(workspace_id, clockify_entry, clockify_tags_id, clockify_api_key, clockify_base_url)

    if timesheet_name:
        add_detail_to_timesheet (timesheet_name, timesheet_detail_data)
    else:
        new_timesheet_name = create_erpnext_timesheet(company, erpnext_employee_id, timesheet_detail_data, timesheet_title )
        timesheet_name = new_timesheet_name

    return timesheet_name


def import_clockify_entries_to_timesheet (workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name, clockify_api_key, clockify_base_url, clockify_tags_id, dienstleistungs_artikel, activity_type):
    entries = fetch_clockify_entries(workspace_id, clockify_user_id, clockify_api_key, clockify_base_url)
    if not entries:
        frappe.msgprint("Keine Einträge gefunden.")
        return
    missing_projects = set()
    imported_entries_count = 0
    error_count = 0
    failed_entries_info = []
    for entry in entries:
        project_name = entry["project"]["name"]
        try:
            duplicate_imports_validation(entry["id"])
            if not validate_project_existence  (project_name):
                if project_name not in missing_projects:
                    missing_projects.add(project_name)
                    create_project_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#Form/Project/New%20Project%201", "Neues Projekt erstellen")
                    frappe.throw(f"Das im Eintrag angegebene Projekt '{project_name}' existiert nicht in ERPNext. Bitte legen Sie das Projekt zuerst an oder korrigieren Sie den Projektnamen im Clockify-Eintrag.{create_project_link}") 
                else:
                    raise Exception(f"Projekt '{project_name}' fehlt weiterhin.")
            
            result = process_clockify_entry_to_erpnext(entry, erpnext_employee_id, erpnext_employee_name, clockify_tags_id, clockify_api_key, clockify_base_url, dienstleistungs_artikel, activity_type)
            if result is not None:
                imported_entries_count += 1
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Fehler bei der Verarbeitung des Clockify-Eintrags. {entry.get('id')}") 
            error_count += 1
            failed_entries_info.append(f"Eintrag {entry.get('id')}: {str(e)}")

    frappe.db.commit() 
    
    if error_count > 0:
        error_log_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Error%20Log/List", "Error log")
        frappe.throw(f"Der Importprozess wurde abgeschlossen: {imported_entries_count} Einträge wurden erfolgreich importiert. Allerdings {error_count} Einträge sind fehlgeschlagen. Bitte überprufen Sie die Fehlerdetails unter {error_log_link}.")
    else:
        timesheet_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Timesheet/List", "Timesheet")
        frappe.msgprint(f"Der Importprozess wurde erfolgreich abgeschlossen: Ingesamt wurden {imported_entries_count} Einträge erfolgreich importiert. Sie können die importierten Daten jetzt im Timesheet-Bereich einsehen, indem Sie den folgenden Link verwenden {timesheet_link}.")


@frappe.whitelist()
def run_clockify_import(user_mapping_name, dienstleistungs_artikel, activity_type):
    clockify_import_settings = frappe.get_doc("Clockify Import Settings")
    workspace_id = clockify_import_settings.workspace_id

    selected_mapping = None
    for user in clockify_import_settings.user_mapping:
        if user.erpnext_employee == user_mapping_name:
            selected_mapping = user
            break
    if not selected_mapping:
        frappe.throw("Ausgewählter user nicht gefunden. Bitte Import nochmals versuchen")
    
    clockify_user_id = selected_mapping.clockify_user_id
    erpnext_employee_id = selected_mapping.erpnext_employee
    erpnext_employee_name = selected_mapping.erpnext_employee_name
    clockify_api_key = clockify_import_settings.get_password('api_key')
    clockify_base_url = clockify_import_settings.clockify_url
    clockify_tags_id = clockify_import_settings.tags_id

    import_clockify_entries_to_timesheet(workspace_id, clockify_user_id, erpnext_employee_id, erpnext_employee_name, clockify_api_key, clockify_base_url, clockify_tags_id, dienstleistungs_artikel, activity_type)

def validate_project_existence (project_name):
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        return False
    return True 

def duplicate_imports_validation (entry_id):
    if frappe.db.exists("Timesheet Detail", {"clockify_entry_id": entry_id}):
        frappe.throw(f"Der Eintrag mit der ID \"{entry_id}\" wurde bereits importiert. Doppelte Importe sind nicht erlaubt. Überprüfen sie die vorhandenen Einträge im Timesheet.") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple
