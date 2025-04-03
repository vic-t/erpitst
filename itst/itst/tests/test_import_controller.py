import unittest
import frappe
from unittest.mock import patch, MagicMock
from itst.itst.integrations.clockify.clockify_service import ClockifyService
from itst.itst.integrations.clockify.erpnext_timesheet_service import ERPNextTimesheetService
from itst.itst.integrations.clockify.import_controller import (
    _calculate_times,
    build_timesheet_detail_data,
    update_clockify_tag,
    process_clockify_entry_to_erpnext,
    import_clockify_entries_to_timesheet,
    validate_project_existence,
)

class TestImportController(unittest.TestCase):
    def test_shouldCalculateTime_whenEntryHasTimeInterval(self):
        entry = {"timeInterval": {
            "start": "2025-01-01T08:00:00Z",
            "duration": "PT1H30M"
            }
        }
        result = _calculate_times(entry)
        self.assertEqual(result["duration_rounded_hhmm"], "1:30")
        self.assertEqual(result["duration_hours"], 1.5)

    def test_shouldBuildTimesheetDetailData_whenClockifyEntryIsProvided(self):
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

        entry = {
            "timeInterval": {
                "start": "2025-01-01T08:00:00Z",
                "end": "2025-01-01T09:30:00Z",
                "duration": "PT1H30M"
            },
            "project": {"name": "Test_Project"},
            "id": "clockify_id_999",
            "billable": True,
            "worspaceid": "ws123",
            "hourlyRate": {"amount": 10000} # 100.00
        }
        result = build_timesheet_detail_data(
            entry,
            dienstleistungs_artikel="test-099",
            activity_type="Planning"
        )
        self.assertEqual(result["project"], "Test_Project")
        self.assertEqual(result["clockify_entry_id"], "clockify_id_999")
        self.assertTrue(result["billable"])
        self.assertEqual(result["billing_rate"], 100.00)
        self.assertEqual(result["category"], "test-099")

        if frappe.db.exists("Project", "Test_Project"):
            frappe.get_doc("Project", "Test_Project").delete()
        
        if frappe.db.exists("Item", "test-099"):
            frappe.get_doc("Item", "test-099").delete()

        frappe.db.commit()

        frappe.db.rollback()
    
    @patch("itst.itst.integrations.clockify.import_controller.ClockifyService.update_clockify_entry")
    def test_shouldUpdateClockifyTag_whenGivenClockifyEntryAndTag(self, mock_update):
        entry = {
            "id": "entry123",
            "projectId": "project123",
            "timeInterval": {
                "start": "2025-01-01T09:00:00Z",
                "end": "2025-01-01T10:00:00Z"
            }
        }
        clockify_service = ClockifyService("api_key", "https://api.clockify.me/api/v1", "ws123")
        update_clockify_tag(clockify_service, entry, "dummy_tag")

        mock_update.assert_called_once_with("entry123", {
            "description": entry.get("description", "No description"),
            "end": entry["timeInterval"]["end"],
            "projectId": entry["projectId"],
            "start": entry["timeInterval"]["start"],
            "tagIds": ["dummy_tag"]
        })
        ####
        call_args = mock_update.call_args[0]
        self.assertEqual(call_args[0], "entry123")
        ####

    @patch("itst.itst.integrations.clockify.import_controller.update_clockify_tag")
    def test_shouldProcessClockifyEntry_whenGivenValidData(self, mock_update_tag):
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

        service = ERPNextTimesheetService(company=self.company_doc.name)

        clockify_service = MagicMock(spec=ClockifyService)

        entry = {
            "project": {"name": "Test_Project"},
            "id": "clockify_id_999",
            "timeInterval": {
                "start": "2025-01-01T08:00:00Z",
                "end": "2025-01-01T09:00:00Z",
                "duration": "PT1H"
            },
            "billable": True,
            "workspaceId": "ws123",
            "hourlyRate": {"amount": 10000}, # 100.00
        }
        
        result_name = process_clockify_entry_to_erpnext(
            entry,
            employee_id="HR-EMP-00099",
            employee_name="Hans",
            activity_type="Planning",
            clockify_tags_id="dummy_tag",
            dienstleistungs_artikel="test-099",
            clockify_service=clockify_service,
            timesheet_service=service
        )

        self.assertIsNotNone(result_name)
        mock_update_tag.assert_called_once()

        if frappe.db.exists("Timesheet", result_name):
            frappe.get_doc("Timesheet", result_name).delete()

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

    @patch("itst.itst.integrations.clockify.import_controller.process_clockify_entry_to_erpnext")
    @patch("itst.itst.integrations.clockify.import_controller.ClockifyService.fetch_clockify_entries")
    def test_shouldImportClockifyEntries_whenEntriesAreFetched(self, mock_fetch, mock_process):

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

        service = ERPNextTimesheetService(company=self.company_doc.name)
        clockify_service = ClockifyService("api_key", "https://api.clockify.me/api/v1", "ws123")

        mock_fetch.return_value = [
            {"id": "entry1", "project": {"name": "Test_Project"}},
            {"id": "entry2", "project": {"name": "Test_Project"}}
        ]

        mock_process.return_value = "TS-2025-99999"

        try:
            import_clockify_entries_to_timesheet(
                timesheet_service=service,
                clockify_service=clockify_service,
                dienstleistungs_artikel="test-099",
                clockify_user_id="user123",
                clockify_tags_id="dummy_tag",
                employee_name="Hans Peter",
                activity_type="Planning",
                employee_id="HR-EMP-00099"
            )
            mock_fetch.assert_called_once()
            self.assertEqual(mock_process.call_count, 2)
        finally:     

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
    
    def test_shouldReturnTrue_whenProjectExists(self):

        self.project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Test_Project",
            "status": "Open"
        }).insert()

        #Look at method "validate_project_existence", and code to understand why.
        self.assertTrue(validate_project_existence("Test_Project"))
        self.assertFalse(validate_project_existence("Test_Project1"))

        if frappe.db.exists("Project", "Test_Project"):
            frappe.get_doc("Project", "Test_Project").delete()