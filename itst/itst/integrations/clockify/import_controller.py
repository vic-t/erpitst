import frappe
from datetime import datetime, timedelta
from typing import List, Dict

from .clockify_service import ClockifyService
from .erpnext_timesheet_service import ERPNextTimesheetService
from .utilities import (
    convert_iso_to_erpnext_datetime,
    parse_duration,
    parse_hhmm_to_minutes,
    round_minutes_to_5,
    minutes_to_hhmm,
    get_week_start_iso,
    build_html_link
)

def validate_project_existence(project_name: str) -> bool:
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        return False
    return True

def duplicate_imports_validation(entry_id: str):
    if frappe.db.exists("Timesheet Detail", {"clockify_entry_id": entry_id}):
        frappe.throw(f"Der Eintrag mit der ID \"{entry_id}\" wurde bereits importiert. Doppelte Importe sind nicht erlaubt. Überprüfen sie die vorhandenen Einträge im Timesheet.") # genauer noch sagen was genau falsch war, welcher ERPnext user und bei welchem projekt, mit zeitstemple

def process_clockify_entry_to_erpnext(
    entry: Dict,
    employee_id: str,
    employee_name: str,
    dienstleistungs_artikel: str,
    activity_type: str,
    timesheet_service: ERPNextTimesheetService,
    clockify_service: ClockifyService,
    clockify_tags_id: str
) -> str:
    from_time = convert_iso_to_erpnext_datetime(entry["timeInterval"]["start"])

    try:
        duration_hours, duration_formatted = parse_duration(entry["timeInterval"]["duration"])
    except ValueError as e:
        # change error to frappe.throw
        frappe.throw(str(e))

    duration_in_minutes = parse_hhmm_to_minutes(duration_formatted)
    duration_rounded_in_minutes = round_minutes_to_5(duration_in_minutes)
    duration_rounded_hhmm = minutes_to_hhmm(duration_rounded_in_minutes)

    datetime_format = "%Y-%m-%d %H:%M:%S"
    from_time_dt = datetime.strptime(from_time, datetime_format)
    to_time_dt = from_time_dt + timedelta(minutes=duration_rounded_in_minutes)
    to_time_str = to_time_dt.strftime(datetime_format)

    project_name = entry["project"]["name"]
    entry_id = entry["id"]
    timesheet_title = f"{employee_name}_{project_name}"
    timesheet_name = timesheet_service.find_timesheet(timesheet_title)
    billing_rate = entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * duration_hours

    timesheet_detail_data = {
        "activity_type": activity_type,
        "from_time": from_time,
        "to_time": to_time_str,
        "duration": duration_rounded_hhmm,
        "hours": duration_hours,
        "project": project_name,
        "billable": entry["billable"],
        "billing_duration": duration_rounded_hhmm,
        "billing_hours": duration_hours,
        "billing_rate": billing_rate,
        "billing_amount": billing_amount,
        "category": dienstleistungs_artikel,
        "remarks": entry.get("description", "Default Remarks"),
        "clockify_entry_id": entry_id
    }

    data = {
        "description": entry.get("description", "No description"),
        "end": entry["timeInterval"]["end"],
        "projectId": entry["projectId"],
        "start": entry["timeInterval"]["start"],
        "tagIds": [clockify_tags_id]
    }
    clockify_service.update_clockify_entry(entry["workspaceId"], entry_id, data)

    if timesheet_name:
        timesheet_service.add_detail_to_timesheet(timesheet_name, timesheet_detail_data)
    else:
        timesheet_name = timesheet_service.create_timesheet(
            employee_id,
            timesheet_title,
            timesheet_detail_data
        )

    return timesheet_name

def import_clockify_entries_to_timesheet(
    clockify_service: ClockifyService,
    timesheet_service: ERPNextTimesheetService,
    workspace_id: str,
    clockify_user_id: str,
    employee_id: str,
    employee_name: str,
    clockify_tags_id: str,
    dienstleistungs_artikel: str,
    activity_type: str
):

    week_start_iso = get_week_start_iso()

    entries = clockify_service.fetch_clockify_entries(workspace_id, clockify_user_id, week_start_iso)
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
            if not validate_project_existence(project_name):
                if project_name not in missing_projects:
                    missing_projects.add(project_name)
                    create_project_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#Form/Project/New%20Project%201", "Neues Projekt erstellen")
                    frappe.throw(f"Das im Eintrag angegebene Projekt '{project_name}' existiert nicht in ERPNext. Bitte legen Sie das Projekt zuerst an oder korrigieren Sie den Projektnamen im Clockify-Eintrag.{create_project_link}")
                else:
                    raise Exception(f"Projekt '{project_name}' fehlt weiterhin.")

            result = process_clockify_entry_to_erpnext(
                entry,
                employee_id,
                employee_name,
                dienstleistungs_artikel,
                activity_type,
                timesheet_service,
                clockify_service,
                clockify_tags_id
            )
            if result is not None:
                imported_entries_count += 1

        except Exception as e:
            frappe.log_error(
                frappe.get_traceback(),
                f"Fehler bei der Verarbeitung des Clockify-Eintrags. ID={entry.get('id')}"
            )
            error_count += 1
            failed_entries_info.append(f"Eintrag {entry.get('id')}: {str(e)}")

    frappe.db.commit()

    if error_count > 0:
        error_log_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Error%20Log/List", "Error log")
        frappe.throw(f"Der Importprozess wurde abgeschlossen: {imported_entries_count} Einträge wurden erfolgreich importiert. Allerdings {error_count} Einträge sind fehlgeschlagen. Bitte überprufen Sie die Fehlerdetails unter {error_log_link}.")
    else:
        timesheet_link = build_html_link("http://erp.itst.ch.localhost:8000/desk#List/Timesheet/List", "Timesheet")
        frappe.msgprint(f"Der Importprozess wurde erfolgreich abgeschlossen: Ingesamt wurden {imported_entries_count} Einträge erfolgreich importiert. Sie können die importierten Daten jetzt im Timesheet-Bereich einsehen, indem Sie den folgenden Link verwenden {timesheet_link}.")

    
    