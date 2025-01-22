#test_run_clockify_import.py

import unittest
import frappe
from unittest.mock import patch, MagicMock
from itst.itst.integrations.clockify.run_clockify_import import run_clockify_import

class TestRunClockifyImport(unittest.TestCase):
    @patch("itst.itst.integrations.clockify.run_clockify_import.import_clockify_entries_to_timesheet")
    @patch("frappe.get_doc")
    def test_shouldRunClockifyImport_whenUserMappingFound(self, mock_get_doc, mock_import):
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

        self.item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "test-099",
            "item_group": "All Item Groups"
        }).insert()

        setttings_mock = MagicMock()
        setttings_mock.workspace_id = "ws123"
        setttings_mock.clockify_url = "https://api.clockify.me/api/v1"
        setttings_mock.tags_id = "dummy_tag"
        setttings_mock.get_password.retun_value = "api_key"

        user_item = MagicMock()
        user_item.erpnext_employee = "HR-EMP-00099"
        user_item.clockify_user_id = "user123"
        user_item.erpnext_employee_name = "Hans"
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
        self.assertEqual(args[5], "Hans")

        if frappe.db.exists("Employee", "HR-EMP-00099"):
            frappe.get_doc("Employee", "HR-EMP-00099").delete()

        if frappe.db.exists("Item", "test-099"):
            frappe.get_doc("Item", "test-099").delete()
        frappe.db.commit()

        frappe.db.rollback()

    @patch("frappe.get_doc")
    def test_shouldThrowError_whenUserMappingNotFound(self, mock_get_doc):
        self.item_doc = frappe.get_doc({
            "doctype": "Item",
            "item_code": "test-099",
            "item_group": "All Item Groups"
        }).insert()

        settings_mock = MagicMock()
        settings_mock.user_mapping = []
        mock_get_doc.return_value = settings_mock

        with self.assertRaises(frappe.ValidationError):
            run_clockify_import(
                user_mapping_name="NotExisting",
                dienstleistungs_artikel="test-099",
                activity_type="Planning"
            )
        
        if frappe.db.exists("Item", "test-099"):
            frappe.get_doc("Item", "test-099").delete()

        frappe.db.commit()