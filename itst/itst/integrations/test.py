import frappe
import re
from datetime import datetime


def test_import_data():
    """Test the creation of a Timesheet with manually provided data."""
    try:
        company = "ITST"
        employee = "HR-EMP-00001"
        initial_time_log = {
            "activity_type": "Planung",
            "from_time": "2024-13-28 09:00:00",
            "to_time": "2024-13-28 12:00:00",
            "billable": True,
            "billing_rate": 50.0,
            "description": "Worked on Project X",
        }

        timesheet_name = create_timesheet_with_initial_log(company, employee, initial_time_log)

        additional_time_log = {
            "activity_type": "Forschung",
            "from_time": "2024-13-28 13:00:00",
            "to_time": "2024-13-28 15:00:00",
            "billable": False,
            "billing_rate": 0.0,
            "description": "Tested Project X",
        }

        add_time_log_to_timesheet(timesheet_name, **additional_time_log)

        frappe.msgprint(f"Test data successfully added to Timesheet {timesheet_name}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Test Import Data Error")
        frappe.throw(f"Test Import Failed: {str(e)}")

def create_timesheet_with_initial_log(company, employee, initial_time_log):
    """Create the parent Timesheet with an initial Time Log entry."""
    try:
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "company": company,
            "employee": employee,
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    **initial_time_log,
                }
            ],
        })
        timesheet.insert()
        frappe.db.commit()
        frappe.msgprint(f"Timesheet {timesheet.name} created successfully.")
        return timesheet.name
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Timesheet Error")
        frappe.throw(f"Failed to create Timesheet: {str(e)}")

def add_time_log_to_timesheet(timesheet_name, activity_type, from_time, to_time, billable, billing_rate, description=None):
    """Add a child Time Log entry to an existing Timesheet."""
    try:
        timesheet = frappe.get_doc("Timesheet", timesheet_name)

        timesheet.append("time_logs", {
            "activity_type": activity_type,
            "from_time": from_time,
            "to_time": to_time,
            "billable": billable,
            "billing_rate": billing_rate,
            "description": description or "",
        })

        timesheet.save()
        frappe.db.commit()
        frappe.msgprint(f"Time Log added to Timesheet {timesheet.name} successfully.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Time Log Error")
        frappe.throw(f"Failed to add Time Log: {str(e)}")
