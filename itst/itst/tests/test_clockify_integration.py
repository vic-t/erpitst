# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and Contributors
# See license.txt
from __future__ import unicode_literals
import unittest

import frappe
import requests
from unittest.mock import patch, MagicMock

from itst.itst.integrations.clockify_integration import (
    parse_duration,
    parse_hhmm_to_minutes,
    minutes_to_hhmm,
    round_minutes_to_5,
    convert_iso_to_erpnext_datetime,
    build_html_link,
    validate_project_existence,
    duplicate_imports_validation,
    create_erpnext_timesheet,
    add_detail_to_timesheet,
    find_timesheet,
    fetch_clockify_entries_for_week,
    update_clockify_entry
)


class TestClockifyIntegration(unittest.TestCase):

    def test_basic_assertion(self):
          self.assertTrue(True, "Dies ist nur ein Dummy-Test, der immer True ist.")

    #Tests for parse_duration
    def test_should_ReturnCorrectDurationAndHour_When_ParsingDuration(self):
        hours, duration_str = parse_duration("PT1H30M")
        self.assertEqual(hours, 1.5)
        self.assertEqual(duration_str, "1:30")

    def test_should_RetrunError_When_InvalidStringIsPassed(self):
        with self.assertRaises(frappe.ValidationError):
            parse_duration("XYZ")

    #Test for parse_hhmm_to_minutes
    def test_should_ReturnNumerIn5MinuteInterval_When_ANumberInhhmmFormatIsGiven(self):
        total_minutes = parse_hhmm_to_minutes("2:05")
        self.assertEqual(total_minutes, 125)

    #Test for minutes_to_hhmm
    def test_should_ReturnNumerinhhmmFormat_When_ANumberIn5MinuteIntervalIsGiven(self):
        hhmm = minutes_to_hhmm(125)
        self.assertEqual(hhmm, "2:05")
    
    #Test for round_minutes_to_5
    def test_should_RoundToTheNext5MinuteIntervalNumber_When_ANumberIsGiven(self):
        self.assertEqual(round_minutes_to_5(123), 125)
        self.assertEqual(round_minutes_to_5(88), 90)

    #Test for convert_iso_to_erpnext_datetime
    def test_should_ConvertISOToErpnextDatetime_When_ISOStringIsGiven(self):
        iso_str = "2025-01-01T10:30:00Z" # UTC
        erp_dt = convert_iso_to_erpnext_datetime(iso_str)

        #In Funktion wird + 1h gerechnet weil Zeitzone Zürich + 1h von UTC ist
        self.assertEqual(erp_dt, "2025-01-01 11:30:00")

    #Test for build_html_link
    def test_should_ReturnCorrectHTMLLink_When_ALinkIsGiven(self):
        link = build_html_link("http://example.com", "Klicke hier")

        self.assertIn("<a href=", link)
        self.assertIn("http://example.com", link)
        self.assertIn("Klicke hier", link)

    #Tests for validate_project_existence
    def test_should_ReturnTrue_When_ProjectDoesExist(self):
        project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Test_Project",
            "status": "Open"
        })
        project_doc.insert()
        self.assertTrue(validate_project_existence("Test_Project"))
        frappe.db.rollback()

    def test_should_ReturnFalse_When_ProjectDoesNotExist(self):
        self.assertFalse(validate_project_existence("Test_Project1"))


    #Tests for duplicate_imports_validation
    def test_should_RetrunError_When_ImportIsAnDuplicate(self):
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
        frappe.db.rollback()

    def test_should_RetrunNone_When_ImportIsNotADuplicate(self):
        self.assertIsNone(duplicate_imports_validation(123456789))

    #Test for fetch_clockify_entries_for_week
    @patch("requests.get")
    def test_should_GetTimeEntriesOfLastWeek_When_APICallIsSuccesfull(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "entry1"},
            {"id": "entry2"}
        ]
        mock_requests_get.return_value = mock_response

        result = fetch_clockify_entries_for_week("ws123", "user456", "dummy_key", "https://api.clockify.me/api/v1")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "entry1")

    @patch("requests.get")
    def test_should_ThrowException_When_APICallIsNotSuccesfull(self, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests_get.return_value = mock_response

        with self.assertRaises(frappe.ValidationError):
            fetch_clockify_entries_for_week("ws123", "user456", "dummy_key", "https://api.clockify.me/api/v1")

    #Test for create_erpnext_timesheet
    def test_should_CreateTimesheet_When_IsBeingPassed(self):
        project_doc = frappe.get_doc({
            "doctype": "Project",
            "project_name": "Test_Project",
            "status": "Open"
        })
        project_doc.insert()

        item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "test-001",
            "item_group": "All Item Groups"
        })
        item_doc.insert()

        company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "TC",
            "default_currency": "CHF",
            "country": "Switzerland"
        })
        company_doc.insert()
         
        employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00001",
            "first_name": "Test",
            "company": "Test_Company",
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2025-01-01",
            "date_of_joining": "2025-08-01"
        })
        employee_doc.insert()

        timesheet_data = {
            "activity_type": "Planning",
            "from_time": "2025-01-01 09:00:00",
            "to_time": "2025-01-01 10:00:00",
            "duration": "1:00",
            "hours": 1.0,
            "project": "Test_Project",
            "billable": True,
            "billing_duration": "1:00",
            "billing_hours": 1.0,
            "billing_rate": 50,
            "billing_amount": 50,
            "category": "test-001",
            "remarks": "Test Remarks",
            "clockify_entry_id": 1234567890
        }

        timesheet_name = create_erpnext_timesheet(
            company = "Test_Company",
            erpnext_employee_id = "HR-EMP-00001",
            timesheet_title = "TestTimesheet",
            timesheet_detail_data = timesheet_data

        )

        self.assertIsNotNone(timesheet_name)

        doc = frappe.get_doc("Timesheet", timesheet_name)
        self.assertEqual(doc.employee, "HR-EMP-00001")
        self.assertEqual(doc.title, "TestTimesheet")
        self.assertEqual(len(doc.time_logs), 1)
        self.assertEqual(doc.time_logs[0].clockify_entry_id, '1234567890')

        frappe.db.rollback()

        #Test for add_detail_to_timesheet
    def test_should_AddTimeLog_When_TimesheetAlreadyExists(self):
        company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "T_C",
            "default_currency": "CHF",
            "country": "Switzerland"
        })
        company_doc.insert()
         
        employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00001",
            "first_name": "Test",
            "company": "Test_Company",
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2025-01-01",
            "date_of_joining": "2025-08-01"
        })
        employee_doc.insert()

        timesheet_doc = frappe.get_doc({
            "doctype": "Timesheet",
            "company": "Test_Company",
            "employee": "HR-EMP-00001",
            "title": "TestTimesheet",
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    "activity_type": "Planning",
                    "from_time": "2025-01-02 09:00:00",
                    "to_time": "2025-01-02 10:00:00",
                    "duration": "1:00",
                    "hours": 1.0,
                    "clockify_entry_id": 1234567890
                }
            ]
        })
        timesheet_doc.insert()
        timesheet_name = timesheet_doc.name

        new_detail = {
            "activity_type": "Planning",
            "from_time": "2025-01-02 14:00:00",
            "to_time": "2025-01-02 15:00:00",
            "duration": "1:00",
            "hours": 1.00,
            "clockify_entry_id": "9876543210"
        }
        returned_name = add_detail_to_timesheet(timesheet_name, new_detail)

        self.assertEqual(returned_name, timesheet_name)

        doc_after = frappe.get_doc("Timesheet", timesheet_name)
        self.assertEqual(len(doc_after.time_logs), 2)
        self.assertEqual(doc_after.time_logs[1].clockify_entry_id, "9876543210")

        frappe.db.rollback()

    #Test for find_timesheet
    def test_should_ReturnTimesheetNameOrNone_When_TimesheetNameisGiven(self):
        company_doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test_Company",
            "abbr": "T_C",
            "default_currency": "CHF",
            "country": "Switzerland"
        })
        company_doc.insert()
         
        employee_doc = frappe.get_doc({
            "doctype": "Employee",
            "naming_series": "HR-EMP-00001",
            "first_name": "Test",
            "company": "Test_Company",
            "status": "Active",
            "gender": "Male",
            "date_of_birth": "2025-01-01",
            "date_of_joining": "2025-08-01"
        })
        employee_doc.insert()

        timesheet_doc = frappe.get_doc({
            "doctype": "Timesheet",
            "company": "Test_Company",
            "employee": "HR-EMP-00001",
            "title": "TestTimesheet",
            "time_logs": [
                {
                    "doctype": "Timesheet Detail",
                    "activity_type": "Planning",
                    "from_time": "2025-01-02 09:00:00",
                    "to_time": "2025-01-02 10:00:00",
                    "duration": "1:00",
                    "hours": 1.0,
                    "clockify_entry_id": 1234567890
                }
            ]
        })
        timesheet_doc.insert()
        timesheet_name = timesheet_doc.name

        #no Timesheet with title "OtherTimesheet"
        result_none = find_timesheet("OtherTimesheet")
        self.assertIsNone(result_none)

        #Timesheet with title that exists
        result_ts = find_timesheet("TestTimesheet")
        self.assertEqual(result_ts, timesheet_name)

        frappe.db.rollback()

    #Test for update_clockify_entry
    @patch("requests.put")
    def test_should_PUTRequestToClockify_When_WhenConnectionToAPIIsSuccessful(self, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp

        entry_data = {
            "id": "entry123",
            "timeInterval": {
                "start": "2025-01-03T09:00:00Z",
                "end": "2025-01-03T10:00:00Z"
            },
            "projectId": "123456789"
        }

        update_clockify_entry(
            workspace_id="testWorkspace",
            entry=entry_data,
            clockify_tags_id="fake_tag",
            clockify_api_key="fake_key",
            clockify_base_url="https://api.clockify.me/api/v1"
        )


        mock_put.assert_called_once()

#Test for update_clockify_entry
    @patch("requests.put")
    def test_should_ThrowsExecption_When_WhenConnectionToAPIIsNotSuccessful(self, mock_put):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_put.return_value = mock_resp

        entry_data = {
            "id": "entry123",
            "timeInterval": {
                "start": "2025-01-03T09:00:00Z",
                "end": "2025-01-03T10:00:00Z"
            },
            "projectId": "123456789"
        }

        


        with self.assertRaises(frappe.ValidationError):
            update_clockify_entry(
                workspace_id="testWorkspace",
                entry=entry_data,
                clockify_tags_id="fake_tag",
                clockify_api_key="fake_key",
                clockify_base_url="https://api.clockify.me/api/v1"
            )
            
            mock_put.assert_called_once()