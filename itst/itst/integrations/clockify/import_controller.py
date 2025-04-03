import frappe
from datetime import datetime, timedelta
from typing import Dict
from frappe.utils import get_url, get_datetime

from .clockify_service import ClockifyService
from .erpnext_timesheet_service import ERPNextTimesheetService
from .utilities import (
    convert_iso_to_erpnext_datetime,
    parse_duration,
    parse_hhmm_to_minutes,
    round_minutes_to_5,
    minutes_to_hhmm,
    convert_erpnext_to_iso_datetime,
    build_html_link
)

def validate_project_existence(project_name: str) -> bool:
    """
    Check if a given project name exists in ERPNext.

    Args: 
        project_name (str): The name of the project to check.
    
    Returns:
        bool: True if the project exists, otherwise False.
    """
    if project_name and not frappe.db.exists("Project", {"project_name": project_name}):
        return False
    return True

def _calculate_times(entry: Dict) -> Dict[str, float]:
    """
    Convert the Clockify time entry's start/duration into ERPNext compatible fields.

    Args: 
        entry (Dict): A dictionary representing the Clockify time entryies containing 'timeInterval' with 'start' and 'duration'.
    
    Returns:
        Dict[str, float | str]: Includes:
            - 'from_time_str' (str),
            - 'to_time_str' (str),
            - 'duration_rounded_hhmm' (str),
            - 'duration_hours' (float)

    Raises:
        frappe.ValidationError: If the duration format is invalid.
    """
    start_str = entry["timeInterval"]["start"]
    user_time_zone = entry["user"]["settings"]["timeZone"] 

    from_time = convert_iso_to_erpnext_datetime(start_str, user_time_zone)

    try:
        duration_hours, duration_formatted = parse_duration(entry["timeInterval"]["duration"])
    except ValueError as e:
        frappe.throw(str(e))

    duration_in_minutes = parse_hhmm_to_minutes(duration_formatted)
    duration_rounded_in_minutes = round_minutes_to_5(duration_in_minutes)
    duration_rounded_hhmm = minutes_to_hhmm(duration_rounded_in_minutes)

    datetime_format = "%Y-%m-%d %H:%M:%S"
    from_time_dt = datetime.strptime(from_time, datetime_format)
    to_time_dt = from_time_dt + timedelta(minutes=duration_rounded_in_minutes)
    to_time_str = to_time_dt.strftime(datetime_format)

    return {
        "from_time_str": from_time,
        "to_time_str": to_time_str,
        "duration_rounded_hhmm": duration_rounded_hhmm,
        "duration_hours": duration_hours
    }

def update_clockify_tag(
    clockify_service: ClockifyService,
    entry: Dict,
    clockify_imported_tag_id: str 
    ) -> None:
    """
    Update a Clockify entry to add or modify a specific tag (clockify_imported_tag_id)

    Args:
        clockify_service (ClockifyService): The service instance to interact with Clockify.
        entry (Dict): The full time entry dictionary form Clockify.
        clockify_imported_tag_id (str): The Tag Id that indicates, the time entrie is imported
    """   
    tag_ids = entry.get("tagIds")

    tag_ids.append(clockify_imported_tag_id)

    clockify_update_data = {
        "description": entry.get("description", "No description"),
        "end": entry["timeInterval"]["end"],
        "projectId": entry["projectId"],
        "start": entry["timeInterval"]["start"],
        "tagIds": tag_ids
    }
    clockify_service.update_clockify_entry(entry["id"], clockify_update_data )

def get_timesheet_kategorie_from_entry(entry: Dict) -> str:
    """
    Determines the appropriate timesheet category for a Timesheet entry.

    Args:
        entry (Dict): The full time entry dictionary form Clockify.
    Returns:
        str: The string of the Kategorie
    """
        
    clockify_entry_tags = [tag.get("id") for tag in entry.get("tags", [])]
    
    mapping_docs = frappe.get_list(
        "Clockify Tag to Kategorie",
        fields=["name", "kategorie"]
    )
    
    for mapping in mapping_docs:
        mapping_doc = frappe.get_doc("Clockify Tag to Kategorie", mapping.name)

        for child in mapping_doc.get("tag_id"):
            child_tag_id = child.tag_id  

            if child_tag_id in clockify_entry_tags:
                return mapping_doc.kategorie

    default_kategorie = frappe.get_value("Timesheet Kategorie", {"standartwert": 1}, "name")
    return default_kategorie

def build_timesheet_detail_data(
    entry: Dict,
    dienstleistungs_artikel: str,
    activity_type: str,
    ) -> Dict:
    """
    Construct a dictionary of fields for a Timesheet Detail entry in ERPNext based on a Clockify time entry.

    Args:
        entry (Dict): The Clockify time entry.
        dienstleistungs_artikel (str): The Item Code representing the service provided.
        activity_type (str): The Activity Type associated with the kind of service provided.

    Returns:
        Dict: A dictionary with keys matching Timesheet Detail fields.
    """

    time_data = _calculate_times(entry)

    project_name = entry["project"]["name"]
    entry_id = entry["id"]

    billing_rate = entry["hourlyRate"]["amount"] / 100
    billing_amount = billing_rate * time_data["duration_hours"]

    kostenstellen = get_timesheet_kategorie_from_entry(entry)

    timesheet_detail_data = {
        "activity_type": activity_type,
        "from_time": time_data["from_time_str"],
        "to_time": time_data["to_time_str"],
        "duration": time_data["duration_rounded_hhmm"],
        "hours": time_data["duration_hours"],
        "kategorie": kostenstellen,
        "project": project_name,
        "billable": entry["billable"],
        "billing_duration": time_data["duration_rounded_hhmm"],
        "billing_hours": time_data["duration_hours"],
        "billing_rate": billing_rate,
        "billing_amount": billing_amount,
        "category": dienstleistungs_artikel,
        "remarks": entry.get("description", "Default Remarks"),
        "clockify_entry_id": entry_id
    }

    return timesheet_detail_data

def set_timesheet_title(entry: Dict, employee_name: str,) -> str:
    """
    Generate a Timesheet title in the format: "Name Benutzer - Name Supportprojekt Jahr-Qx"

    Args:
        entry (Dicts): The single Clockify time entry dictionary.
        employee_name (str): The employee's name in ERPNext.

    Returns:
        str: The name for the Timesheet in ERPNext.
    """
    project_name = entry["project"]["name"]
    entry_start = entry["timeInterval"]["start"]

    start_dt = get_datetime(entry_start)

    current_year = start_dt.year
    current_quarter = (start_dt.month - 1) // 3 + 1

    return f"{employee_name} - {project_name} {current_year}-Q{current_quarter}"

def process_clockify_entry_to_erpnext(
    entry: Dict,
    employee_id: str,
    employee_name: str,
    activity_type: str,
    clockify_imported_tag_id: str,
    dienstleistungs_artikel: str,
    clockify_service: ClockifyService,
    timesheet_service: ERPNextTimesheetService,
    ) -> str:
    """
    Processes a single Clockify entry and imports it into ERPNext as a Timesheet Detail.

    If a Timesheet (Draft) with the pattern '{employee_name}_{project_name}' exists, a new detail will be appended. Otherwise, a new timesheet is created, updates the entry in Clockify by a specific tag.

    Args:
        entry (Dicts): The single Clockify time entry dictionary.
        employee_id (str): The ERPNext employee ID.
        employee_name (str): The employee's name in ERPNext.
        activity_type (str): The Activity Type associated with the kind of service provided.
        clockify_imported_tag_id (str): The tag Id to be set on the Clockify entry.
        dienstleistungs_artikel (str): The Item Code representing the service provided. 
        clockify_service (ClockifyService): The service to interact with Clockify.
        timesheet_service (ERPNextTimesheetService): The service to interact with ERPNext Timesheets.
    
    Returns:
        str: The name of the Timesheet (existing or newly created) in ERPNext.
    """

    timesheet_title = set_timesheet_title(entry, employee_name)
    timesheet_name = timesheet_service.find_timesheet(timesheet_title)

    timesheet_detail_data = build_timesheet_detail_data(
        entry,
        dienstleistungs_artikel,
        activity_type,
    )

    if timesheet_name:
        timesheet_service.add_detail_to_timesheet(timesheet_name, timesheet_detail_data)
    else:
        timesheet_name = timesheet_service.create_timesheet(
            employee_id,
            timesheet_title,
            timesheet_detail_data
        )
    
    update_clockify_tag(
        clockify_service,
        entry,
        clockify_imported_tag_id 
    )

    return timesheet_name

def get_dienstleistungsartikel_for_entry(
    entry: dict, 
    clockify_tags_mapping: list
) -> str:
    """
    Sucht in clockify_tags_mapping nach einem passenden Tag (Name und ID). Gibt das 'artikel' zurück, wenn gefunden, sonst None.

    Args:
        entry (Dicts): The single Clockify time entry dictionary.
        clockify_tags_mapping (list): List of Tags (Name, ID and Artikel).

    Returns:
        str: The Artikel of which the Tag belongs to.
    """
    clockify_entry_tags = entry.get("tags", [])

    for row in clockify_tags_mapping:
        for clockify_tag in clockify_entry_tags:
            if (
                row.tag_name == clockify_tag.get("name") and
                row.tag_id == clockify_tag.get("id")
            ):
                return row.artikel
    
    return None


def import_clockify_entries_to_timesheet(
    timesheet_service: ERPNextTimesheetService,
    clockify_service: ClockifyService,
    dienstleistungs_artikel: str,
    clockify_user_id: str,
    clockify_imported_tag_id: str,
    employee_name: str,
    activity_type: str,
    employee_id: str,
    clockify_start_time: str,
    clockify_end_time: str,
    clockify_tags_mapping: list
    ):
    """
    Import multiple time entries from Clockify for a specific user into ERPNext Timesheets.

    Validates each entry (checking for project existence). If valid, it processes the entry to create or update a Timesheet in ERPNext an updates the entry in Clockify

    Args:
        timesheet_service (ERPNextTimesheetService): The service to interact with ERPNext Timesheets.
        clockify_service (ClockifyService): The service to interact with Clockify.
        dienstleistungs_artikel (str): The Item Code representing the service provided. 
        clockify_user_id (str): The Clockify user ID whose entries are to be fetched.
        clockify_imported_tag_id (str): The tag Id to be set on the Clockify entry.
        employee_name (str): The employee's name in ERPNext.
        activity_type (str): The Activity Type associated with the kind of service provided.
        employee_id (str): The ERPNext employee ID.
        clockify_start_time (str): Start date and time for time entries import.
        clockify_end_time (str): End date and time for time entries import.
    
    Returns:
        None: Raises an exception if some imports failed or prints a success message otherwise.

    Raises:
        Exception: If a project does not exist in ERPNext or a duplicate is detected, 
            the relevant errors are thrown or logged. Also raises if any entry processing fails.
    """
    start_iso = convert_erpnext_to_iso_datetime(clockify_start_time)
    end_iso = convert_erpnext_to_iso_datetime(clockify_end_time)

    entries = clockify_service.fetch_clockify_entries(clockify_user_id, clockify_imported_tag_id, start_iso, end_iso)
    if not entries:
        frappe.msgprint("Keine Einträge gefunden.")
        return

    missing_projects = set()
    imported_entries_count = 0
    error_count = 0
    failed_entries_info = []

    base_url = get_url()
    
    for entry in entries:
        project_name = entry["project"]["name"]
        try:
            if not validate_project_existence(project_name):
                if project_name not in missing_projects:
                    missing_projects.add(project_name)
                    create_project_link = build_html_link(f"{base_url}/desk#Form/Project/New%20Project%201", "Neues Projekt erstellen")
                    frappe.throw(
                        title="Project Error",
                        msg=f"Das im Eintrag angegebene Projekt '{project_name}' existiert nicht in ERPNext. Bitte legen Sie das Projekt zuerst an oder korrigieren Sie den Projektnamen im Clockify-Eintrag.{create_project_link}"
                        )
                else:
                    raise Exception(f"Projekt '{project_name}' fehlt weiterhin.")

            overridden_artikel = get_dienstleistungsartikel_for_entry(entry, clockify_tags_mapping)

            dienstleistungs_artikel = overridden_artikel or dienstleistungs_artikel

            result = process_clockify_entry_to_erpnext(
                entry,
                employee_id,
                employee_name,
                activity_type,
                clockify_imported_tag_id,
                dienstleistungs_artikel,
                clockify_service,
                timesheet_service,
            )
            frappe.db.commit()
            if result is not None:
                imported_entries_count += 1
        except Exception as e:
            frappe.db.rollback()
            error_count += 1
            failed_entries_info.append(f"Eintrag {entry.get('id')}: {str(e)}")

    if error_count > 0:
        error_log_link = build_html_link(f"{base_url}/desk#List/Error%20Log/List", "Error log")
        frappe.log_error(
            title="Clockify Import Error",
            message=f"Der Import der Zeiteinträge war nicht vollständig erfolgreich. Bitte loggen Sie sich in Clockify ein und überprüfen Sie alle Zeiteinträge, bei denen kein Tag vorhanden ist (in ERP). Vergleichen Sie jeweils, ob der Projektname mit dem in ERPNext übereinstimmt. Falls Sie Anpassungen an einem Timesheet vornehmen müssen, entfernen Sie bitte den Tag, damit der Zeiteintrag problemlos importiert werden kann. Bei weiteren Fragen oder für genauere Anleitungen schauen Sie bitte im Wiki nach. \n {failed_entries_info}"
        )

        frappe.throw(
            title="Error",
            msg=f"Der Importprozess wurde abgeschlossen: {imported_entries_count} Einträge wurden erfolgreich importiert. Allerdings {error_count} Einträge sind fehlgeschlagen. Bitte überprufen Sie die Fehlerdetails unter {error_log_link}."
            )

    else:
        timesheet_link = build_html_link(f"{base_url}/desk#List/Timesheet/List", "Timesheet")
        frappe.msgprint(
            title="Success",
            indicator="green",
            msg=f"Der Importprozess wurde erfolgreich abgeschlossen: Ingesamt wurden {imported_entries_count} Einträge erfolgreich importiert. Sie können die importierten Daten jetzt im Timesheet-Bereich einsehen, indem Sie den folgenden Link verwenden {timesheet_link}."
            )
