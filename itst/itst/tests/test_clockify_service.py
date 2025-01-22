# test_clockify_service.py

import unittest
import frappe
from unittest.mock import patch, MagicMock
from itst.itst.integrations.clockify.clockify_service import ClockifyService

class TestClockifyService(unittest.TestCase):
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