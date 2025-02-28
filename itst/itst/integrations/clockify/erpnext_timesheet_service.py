import frappe
from typing import Optional, Dict

class ERPNextTimesheetService:
    """
    A service class for interacting with the ERPNext Timesheet Doctype.

    This class supports creating new Timesheets, adding new time logs to existing Timesheets, and searching for existing Timesheets by title.
    """
    def __init__(self, company: str):
        """
        Initialize the service with a specific company.

        Args:
            company (str): The anme of the company to be used for in Timesheets.
        """
        self.company = company
    
    def create_timesheet(self, erpnext_employee_id: str, timesheet_title: str, timesheet_detail_data: Dict) -> str:
        """
        Create a new Timesheet document in ERPNext with one Timesheet Detail entry.

        Args:
            erpnext_employee_id (str): The ID of the Employee in ERPNext.
            timesheet_title (str): The title to be assigned to the newly created Timesheet.
            timesheet_detail_data (Dict): A dictionary of fields used to create the Timesheet Detail record.

        Returns:
            str: The name of the newly created Timesheet in ERPNext.
        """
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "company": self.company,
            "employee": erpnext_employee_id,
            "title": timesheet_title ,
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    **timesheet_detail_data,
                }
            ],
        })    
        timesheet.insert()
        return timesheet.name

    def add_detail_to_timesheet(self, timesheet_name: str, timesheet_detail_data: Dict) -> str:
        """
        Add a new Timesheet Detail entry to existing Timesheet.

        Args:
            timesheet_name (str): The name of the existing Timesheet.
            timesheet_detail_data (Dict): A dictionary of fields for creating a new Timesheet Detail record.

        Returns:
            str: The name of the updated Timesheet.
        """
        timesheet = frappe.get_doc("Timesheet", timesheet_name)

        for time_log in timesheet.time_logs:
            time_log.from_time = str(time_log.from_time)
            time_log.to_time = str(time_log.to_time)

        timesheet.append("time_logs", {
            "doctype": "Timesheet Detail",
            **timesheet_detail_data
        })
        timesheet.save()
        return timesheet.name
    
    def find_timesheet(self, timesheet_title: str) -> Optional[str]:
        """
        Search for a Draft Timesheet by title, and looks if the status of the Timsheet is Draft.

        Args:
            timesheet_title (str): The title of the Timesheet to be searched for.

        Returns:
            Optional[str]: The name of the found Timesheet, or None if not found.
        """
        timesheets = frappe.get_list(
            "Timesheet",
            filters={
                "title": timesheet_title ,
                "status": "Draft"
                },  # Filtering by title and Draft documents
            fields=["name"]
        )
        return timesheets[0].name if timesheets else None