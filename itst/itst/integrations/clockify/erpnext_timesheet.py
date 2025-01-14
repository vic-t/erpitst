import frappe
from typing import Optional, Dict

class ERPNextTimesheet:
    def __init__(self, company: str):
        self.company = company
    
    def create_timesheet(self, erpnext_employee_id: str, timesheet_title: str, timesheet_detail_data: Dict) -> str:
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
        timesheets = frappe.get_list(
            "Timesheet",
            filters={
                "title": timesheet_title ,
                "status": "Draft"
                },  # Filtering by title and Draft documents
            fields=["name"]
        )
        return timesheets[0].name if timesheets else None