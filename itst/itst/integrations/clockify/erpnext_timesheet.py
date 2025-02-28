import frappe

def create_erpnext_timesheet(company, erpnext_employee_id, timesheet_detail_data, timesheet_title ):
    timesheet = frappe.get_doc({
        "doctype": "Timesheet",
        "company": company,
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

def add_detail_to_timesheet (timesheet_name, timesheet_detail_data):
    timesheet = frappe.get_doc("Timesheet", timesheet_name)

    for time_log in timesheet.time_logs:
        time_log.from_time = str(time_log.from_time)
        time_log.to_time = str(time_log.to_time)
    
    timesheet.append("time_logs", {
        "doctype": "Timesheet Detail",
        **timesheet_detail_data,
    })
    timesheet.save()
    return timesheet.name

def find_timesheet(timesheet_title ):
    timesheets = frappe.get_list(
        "Timesheet",
        filters={
            "title": timesheet_title ,
            "status": "Draft"
            },  # Filtering by title and Draft documents
        fields=["name"]
    )
    return timesheets[0].name if timesheets else None