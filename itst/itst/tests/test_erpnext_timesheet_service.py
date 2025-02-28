import unittest
import frappe
from itst.itst.integrations.clockify.erpnext_timesheet_service import ERPNextTimesheetService

class TestERPNextTimesheetService(unittest.TestCase):
    def test_shouldCreateTimesheet_whenValidDataPassed(self):
        self.company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "TC",
            "default_currency": "CHF",
            "country": "Switzerland"
        }).insert()

        self.employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00099",
            "first_name": "Hans",
            "company": self.company_doc.name,
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2000-01-01",
            "date_of_joining": "2025-01-01"
        }).insert()

        self.project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Test_Project",
            "status": "Open"
        }).insert()

        self.item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "test-099",
            "item_group": "All Item Groups"
        }).insert()

        timesheet_service = ERPNextTimesheetService(company=self.company_doc.name)

        timesheet_data = {
            "activity_type": "Planning",
            "from_time": "2025-01-01 09:00:00",
            "to_time": "2025-01-01 10:00:00",
            "duration": "1:00",
            "hours": 1.0,
            "project": self.project_doc.name,
            "billable": True,
            "billing_duration": "1:00",
            "billing_hours": 1.0,
            "billing_rate": 50,
            "billing_amount": 50,
            "category": self.item_doc.name,
            "remarks": "Test Remarks",
            "clockify_entry_id": 1234567890
        }

        timesheet_name = timesheet_service.create_timesheet(
            erpnext_employee_id = self.employee_doc.name,
            timesheet_title = "TestTimesheet123",
            timesheet_detail_data = timesheet_data
        )

        self.assertIsNotNone(timesheet_name)

        doc = frappe.get_doc("Timesheet", timesheet_name)
        self.assertEqual(doc.employee, self.employee_doc.name)
        self.assertEqual(doc.title, "TestTimesheet123")
        self.assertEqual(len(doc.time_logs), 1)
        self.assertEqual(doc.time_logs[0].clockify_entry_id, '1234567890')

        if frappe.db.exists("Timesheet", timesheet_name):
            frappe.get_doc("Timesheet", timesheet_name).delete()
            
        if frappe.db.exists("Company", "Test_Company"):
            frappe.get_doc("Company", "Test_Company").delete()
  
        if frappe.db.exists("Employee", "HR-EMP-00099"):
            frappe.get_doc("Employee", "HR-EMP-00099").delete()
        
        if frappe.db.exists("Project", "Test_Project"):
            frappe.get_doc("Project", "Test_Project").delete()
        
        if frappe.db.exists("Item", "test-099"):
            frappe.get_doc("Item", "test-099").delete()

        frappe.db.commit()

        frappe.db.rollback()

    def test_shouldAddTimeLog_whenTimesheetAlreadyExists(self):
        self.company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "TC",
            "default_currency": "CHF",
            "country": "Switzerland"
        }).insert()

        self.employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00099",
            "first_name": "Hans",
            "company": self.company_doc.name,
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2000-01-01",
            "date_of_joining": "2025-01-01"
        }).insert()

        timesheet_service = ERPNextTimesheetService(company=self.company_doc.name)

        timesheet_name = timesheet_service.create_timesheet(
            erpnext_employee_id=self.employee_doc.name,
            timesheet_title="TestTimesheet",
            timesheet_detail_data={
                "activity_type": "Planning",
                "from_time": "2025-01-02 09:00:00",
                "to_time": "2025-01-02 10:00:00",
                "duration": "1:00",
                "hours": 1.0,
                "clockify_entry_id": "init_123"
            }
        )

        new_detail = {
            "activity_type": "Planning",
            "from_time": "2025-01-02 14:00:00",
            "to_time": "2025-01-02 15:00:00",
            "duration": "1:00",
            "hours": 1.00,
            "clockify_entry_id": "9876543210"
        }
        returned_name = timesheet_service.add_detail_to_timesheet(timesheet_name, new_detail)
        self.assertEqual(returned_name, timesheet_name)

        doc_after = frappe.get_doc("Timesheet", timesheet_name)
        self.assertEqual(len(doc_after.time_logs), 2)
        self.assertEqual(doc_after.time_logs[1].clockify_entry_id, "9876543210")

        if frappe.db.exists("Timesheet", timesheet_name):
            frappe.get_doc("Timesheet", timesheet_name).delete()

        if frappe.db.exists("Company", "Test_Company"):
            frappe.get_doc("Company", "Test_Company").delete()

        if frappe.db.exists("Employee", "HR-EMP-00099"):
            frappe.get_doc("Employee", "HR-EMP-00099").delete()

        frappe.db.rollback()

    def test_shouldReturnTimesheetNameOrNone_whenTitleIsGiven(self):
        self.company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "TC",
            "default_currency": "CHF",
            "country": "Switzerland"
        }).insert()

        self.employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00099",
            "first_name": "Hans",
            "company": self.company_doc.name,
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2000-01-01",
            "date_of_joining": "2025-01-01"
        }).insert()

        timesheet_service = ERPNextTimesheetService(company=self.company_doc.name)

        timesheet_name = timesheet_service.create_timesheet(
            erpnext_employee_id=self.employee_doc.name,
            timesheet_title="VeryUniqueTestTimsheet",
            timesheet_detail_data={
                "activity_type": "Planning",
                "from_time": "2025-01-02 09:00:00",
                "to_time": "2025-01-02 10:00:00",
                "duration": "1:00",
                "hours": 1.0,
                "clockify_entry_id": "init_123"
            }
        )
        # should exist
        found_name = timesheet_service.find_timesheet("VeryUniqueTestTimsheet")
        self.assertEqual(found_name, timesheet_name)

        # should be None
        self.assertIsNone(timesheet_service.find_timesheet("NonExistentTimesheet"))

        if frappe.db.exists("Timesheet", timesheet_name):
            frappe.get_doc("Timesheet", timesheet_name).delete()

        if frappe.db.exists("Company", "Test_Company"):
            frappe.get_doc("Company", "Test_Company").delete()

        if frappe.db.exists("Employee", "HR-EMP-00099"):
            frappe.get_doc("Employee", "HR-EMP-00099").delete()
        frappe.db.commit()
        frappe.db.rollback()