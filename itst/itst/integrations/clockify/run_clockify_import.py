import frappe
from .clockify_service import ClockifyService
from .erpnext_timesheet_service import ERPNextTimesheetService
from .import_controller import import_clockify_entries_to_timesheet

@frappe.whitelist()
def run_clockify_import(user_mapping_name: str, clockify_start_time: str, clockify_end_time: str):
    """
    Whitelisted method to import Clockify entries into ERPNext Timesheet based on user selection.

    Args:
        user_mapping_name (str): The ERPNext employee Id, ERPNext employee name and the Clockify user Id mapped.
        clockify_start_time (str): Start date and time for time entries import. 
        clockify_end_time (str): End date and time for time entries import. 

    Raises:
        frappe.ValidationError: If the selected user mapping is not found in 'Clockify Import Settings'.
    """
    clockify_import_settings = frappe.get_doc("Clockify Import Settings")

    selected_user_mapping = None
    for user in clockify_import_settings.user_mapping:
        if user.erpnext_employee == user_mapping_name:
            selected_user_mapping = user
            break
    if not selected_user_mapping:
        frappe.throw("Ausgewählter User nicht gefunden.")


    clockify_user_id = selected_user_mapping.clockify_user_id
    erpnext_employee_id = selected_user_mapping.erpnext_employee
    erpnext_employee_name = selected_user_mapping.erpnext_employee_name
    clockify_api_key = clockify_import_settings.get_password("api_key")
    clockify_workspace_id = clockify_import_settings.workspace_id
    clockify_base_url = clockify_import_settings.clockify_url
    clockify_imported_tag_id = clockify_import_settings.imported_tag_id

    clockify_service = ClockifyService(
        api_key = clockify_api_key,
        base_url = clockify_base_url, 
        workspace_id = clockify_workspace_id,
    )

    timesheet_service = ERPNextTimesheetService(company="ITST Gmbh")

    import_clockify_entries_to_timesheet(
        timesheet_service,
        clockify_service,       
        clockify_user_id,
        clockify_imported_tag_id,
        erpnext_employee_name,
        erpnext_employee_id,
        clockify_start_time,
        clockify_end_time,
    )