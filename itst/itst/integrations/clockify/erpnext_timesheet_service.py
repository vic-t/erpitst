import frappe
from typing import Optional, Dict

class ERPNextTimesheetService:
    def __init__(self, company: str, timesheet_detail_data: Dict, timesheet_title: str):
        self.company = company
        self.timesheet_detail_data = timesheet_detail_data
        self.timesheet_title = timesheet_title
    
    def create_timesheet(self, erpnext_employee_id: str) -> str:
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "company": self.company,
            "employee": erpnext_employee_id,
            "title": self.timesheet_title ,
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    **self.timesheet_detail_data,
                }
            ],
        })    
        timesheet.insert()
        return timesheet.name

    def add_detail_to_timesheet(self, timesheet_name: str) -> str:
        timesheet = frappe.get_doc("Timesheet", timesheet_name)

        for time_log in timesheet.time_logs:
            time_log.from_time = str(time_log.from_time)
            time_log.to_time = str(time_log.to_time)

        timesheet.append("time_logs", {
            "doctype": "Timesheet Detail",
            **self.timesheet_detail_data
        })
        timesheet.save()
        return timesheet.name
    
    def find_timesheet(self) -> Optional[str]:
        timesheets = frappe.get_list(
            "Timesheet",
            filters={
                "title": self.timesheet_title ,
                "status": "Draft"
                },  # Filtering by title and Draft documents
            fields=["name"]
        )
        return timesheets[0].name if timesheets else None