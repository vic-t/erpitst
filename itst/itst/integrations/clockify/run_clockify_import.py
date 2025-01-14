import frappe
from .clockify_service import ClockifyService
from .erpnext_timesheet_service import ERPNextTimesheetService
from .import_controller import import_clockify_entries_to_timesheet

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
        frappe.throw("Ausgewählter User nicht gefunden.")

    clockify_user_id = selected_mapping.clockify_user_id
    erpnext_employee_id = selected_mapping.erpnext_employee
    erpnext_employee_name = selected_mapping.erpnext_employee_name
    clockify_api_key = clockify_import_settings.get_password("api_key")
    clockify_base_url = clockify_import_settings.clockify_url
    clockify_tags_id = clockify_import_settings.tags_id

    clockify_service = ClockifyService(
        api_key=clockify_api_key,
        base_url=clockify_base_url
    )

    timesheet_service = ERPNextTimesheetService(company="ITST")

    import_clockify_entries_to_timesheet(
        clockify_service,
        timesheet_service,
        workspace_id,
        clockify_user_id,
        erpnext_employee_id,
        erpnext_employee_name,
        clockify_tags_id,
        dienstleistungs_artikel,
        activity_type
    )