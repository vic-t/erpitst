# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and Contributors
# See license.txt
from __future__ import unicode_literals
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
    duplicate_imports_validation
)
from itst.itst.integrations.clockify.run_clockify_import import run_clockify_import
from itst.itst.integrations.clockify.utilities import (
    parse_duration,
    parse_hhmm_to_minutes,
    minutes_to_hhmm,
    round_minutes_to_5,
    convert_iso_to_erpnext_datetime,
    build_html_link,
    get_week_start_iso
)


class TestClockifyIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "TC",
            "default_currency": "CHF",
            "country": "Switzerland"
        }).insert()

        cls.employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00099",
            "first_name": "Hans",
            "company": cls.company_doc.name,
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2000-01-01",
            "date_of_joining": "2025-01-01"
        }).insert()

        cls.project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Test_Project",
            "status": "Open"
        }).insert()

        cls.item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "test-099",
            "item_group": "All Item Groups"
        }).insert()

    @classmethod
    def tearDownClass(cls):
        # remove that doc
        if frappe.db.exists("Company", "Test_Company"):
            frappe.get_doc("Company", "Test_Company").delete()
            
        if frappe.db.exists("Employee", "HR-EMP-00099"):
            frappe.get_doc("Employee", "HR-EMP-00099").delete()
        
        if frappe.db.exists("Project", "Test_Project"):
            frappe.get_doc("Project", "Test_Project").delete()
        
        if frappe.db.exists("Item", "test-099"):
            frappe.get_doc("Item", "test-099").delete()
        frappe.db.commit()
        super().tearDownClass()

    # --------------------------------------------
    # UTILITIES.PY TESTS
    # --------------------------------------------
    def test_shouldReturnCorrectDurationAndHours_whenParsingDuration(self):
        hours, duration_str = parse_duration("PT1H30M")
        self.assertEqual(hours, 1.5)
        self.assertEqual(duration_str, "1:30")

    def test_shouldThrowError_whenParsingInvalidDurationString(self):
        with self.assertRaises(ValueError):
            parse_duration("XYZ")

    #Test for parse_hhmm_to_minutes
    def test_shouldReturnMinutes_whenGivenHHmmFormat(self):
        total_minutes = parse_hhmm_to_minutes("2:05")
        self.assertEqual(total_minutes, 125)

    #Test for minutes_to_hhmm
    def test_shouldReturnHHmm_whenGivenTotalMinutes(self):
        hhmm = minutes_to_hhmm(125)
        self.assertEqual(hhmm, "2:05")
    
    #Test for round_minutes_to_5
    def test_shouldRoundToNearest5Minutes_whenGivenAnyNumberOfMinutes(self):
        self.assertEqual(round_minutes_to_5(123), 125)
        self.assertEqual(round_minutes_to_5(88), 90)

    #Test for convert_iso_to_erpnext_datetime
    def test_shouldConvertISOToErpnextDatetime_whenGivenISOString(self):
        # UTC 10:30 => +1h => 11:30
        iso_str = "2025-01-01T10:30:00Z" # UTC
        erp_dt = convert_iso_to_erpnext_datetime(iso_str)
        self.assertEqual(erp_dt, "2025-01-01 11:30:00")

    #Test for build_html_link
    def test_shouldReturnCorrectHtmlLink_whenGivenUrlAndText(self):
        link = build_html_link("http://example.com", "Klicke hier")
        self.assertIn("<a href=", link)
        self.assertIn("http://example.com", link)
        self.assertIn("Klicke hier", link)
    
    #Test for get_week_start_iso
    def test_shouldReturnWeekStartIso_whenCalled(self):
        iso_val = get_week_start_iso()
        self.assertIn("T00:00:00Z", iso_val)

    # --------------------------------------------
    # ERPNextTimesheetService TESTS
    # --------------------------------------------
    #Test for create_erpnext_timesheet
    def test_shouldCreateTimesheet_whenValidDataPassed(self):
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
            timesheet_title = "TestTimesheet",
            timesheet_detail_data = timesheet_data
        )

        self.assertIsNotNone(timesheet_name)

        doc = frappe.get_doc("Timesheet", timesheet_name)
        self.assertEqual(doc.employee, self.employee_doc.name)
        self.assertEqual(doc.title, "TestTimesheet")
        self.assertEqual(len(doc.time_logs), 1)
        self.assertEqual(doc.time_logs[0].clockify_entry_id, '1234567890')

        frappe.db.rollback()

    #Test for add_detail_to_timesheet
    def test_shouldAddTimeLog_whenTimesheetAlreadyExists(self):
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

        frappe.db.rollback()

    #Test for find_timesheet
    def test_shouldReturnTimesheetNameOrNone_whenTitleIsGiven(self):
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

        frappe.db.rollback()

    # --------------------------------------------
    # import_controller.py tests
    # --------------------------------------------
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
            employee_name="Hans Ruedi",
            activity_type="Planning",
            clockify_tags_id="dummy_tag",
            dienstleistungs_artikel="test-099",
            clockify_service=clockify_service,
            timesheet_service=service
        )

        self.assertIsNotNone(result_name)
        mock_update_tag.assert_called_once()

        frappe.db.rollback()

    @patch("itst.itst.integrations.clockify.import_controller.process_clockify_entry_to_erpnext")
    @patch("itst.itst.integrations.clockify.import_controller.ClockifyService.fetch_clockify_entries")
    def test_shouldImportClockifyEntries_whenEntriesAreFetched(self, mock_fetch, mock_process):

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
            
            frappe.db.rollback()

    #Tests for duplicate_imports_validation
    def test_shouldThrowError_whenDuplicateImportAttempted(self):
        timesheet_doc = frappe.get_doc({
            "doctype": "Timesheet",
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    "clockify_entry_id": 1234567890
                }
            ],
        })  
        timesheet_doc.insert()

        with self.assertRaises(frappe.ValidationError):
            duplicate_imports_validation(1234567890)

        self.assertIsNone(duplicate_imports_validation(9876543210))
        frappe.db.rollback()
    
    #Tests for validate_project_existence
    def test_shouldReturnTrue_whenProjectExists(self):
        #Look at method "validate_project_existence", and code to understand why.
        self.assertTrue(validate_project_existence("Test_Project"))
        self.assertFalse(validate_project_existence("Test_Project1"))

    # --------------------------------------------
    # RUN_CLOCKIFY_IMPORT.PY TESTS
    # --------------------------------------------
    @patch("itst.itst.integrations.clockify.run_clockify_import.import_clockify_entries_to_timesheet")
    @patch("frappe.get_doc")
    def test_shouldRunClockifyImport_whenUserMappingFound(self, mock_get_doc, mock_import):
        setttings_mock = MagicMock()
        setttings_mock.workspace_id = "ws123"
        setttings_mock.clockify_url = "https://api.clockify.me/api/v1"
        setttings_mock.tags_id = "dummy_tag"
        setttings_mock.get_password.retun_value = "api_key"

        user_item = MagicMock()
        user_item.erpnext_employee = "HR-EMP-00099"
        user_item.clockify_user_id = "user123"
        user_item.erpnext_employee_name = "Hans Peter"
        setttings_mock.user_mapping = [user_item]

        mock_get_doc.return_value = setttings_mock

        run_clockify_import(
            user_mapping_name="HR-EMP-00099",
            dienstleistungs_artikel="test-099",
            activity_type="Planning"
        )

        mock_import.assert_called_once()
        args, kwargs = mock_import.call_args
        self.assertEqual(args[3], "user123")
        self.assertEqual(args[7], "HR-EMP-00099")
        self.assertEqual(args[5], "Hans Peter")

    @patch("frappe.get_doc")
    def test_shouldThrowError_whenUserMappingNotFound(self, mock_get_doc):
        settings_mock = MagicMock()
        settings_mock.user_mapping = []
        mock_get_doc.return_value = settings_mock

        with self.assertRaises(frappe.ValidationError):
            run_clockify_import(
                user_mapping_name="NotExisting",
                dienstleistungs_artikel="test-099",
                activity_type="Planning"
            )
 
    # --------------------------------------------
    # CLOCKIFY_SERVICE.PY TESTS
    # --------------------------------------------
    #Test for fetch_clockify_entries
    @patch("requests.request")
    def test_shouldGetTimeEntries_whenAPICallSucceeds(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "entry1"},
            {"id": "entry2"}
        ]
        mock_requests_get.return_value = mock_response

        service = ClockifyService("api_key", "https://api.clockify.me/api/v1", "ws123")
        result = service.fetch_clockify_entries("user456", "2025-01-01T00:00:00Z")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "entry1")

    @patch("requests.request")
    def test_shouldThrowException_whenAPICallFails(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_get.return_value = mock_response

        with self.assertRaises(frappe.ValidationError):
            service = ClockifyService("api_key", "https://api.clockify.me/api/v1", "ws123")
            service.fetch_clockify_entries("user123", "2025-01-01T00:00:00Z")

    #Test for update_clockify_entry
    @patch("requests.request")
    def test_shouldPUTClockifyEntry_whenConnectionIsSuccessful(self, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp

        service = ClockifyService("api_key", "https://api.clockify.me/api/v1", "ws123")

        entry_data = {
            "id": "entry123",
            "timeInterval": {
                "start": "2025-01-03T09:00:00Z",
                "end": "2025-01-03T10:00:00Z"
            },
            "projectId": "123456789",
            "tagIds": ["dummy_tag"]
        }

        service.update_clockify_entry("entry123", entry_data)

        mock_put.assert_called_once()

    #Test for update_clockify_entry
    @patch("requests.request")
    def test_shouldThrowException_whenConnectionNotSuccessful(self, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_put.return_value = mock_resp

        entry_data = {
            "id": "entry123",
            "timeInterval": {
                "start": "2025-01-03T09:00:00Z",
                "end": "2025-01-03T10:00:00Z"
            },
            "projectId": "123456789"
        }
        service = ClockifyService(
            api_key="fake_key",
            base_url="https://api.clockify.me/api/v1",
            workspace_id="testWorkspace"
        )
        with self.assertRaises(frappe.ValidationError):
            service.update_clockify_entry(
                entry_id="entry123",
                data=entry_data
            )

            mock_put.assert_called_once()