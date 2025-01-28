import requests
import frappe
from typing import List, Dict, Optional

DEFAULT_PAGE_NUMBER = 1
MAX_PAGE_SIZE = 5000

class ClockifyService:
    """
    A service class for interacting with the Clockify API.

    This class handles requests such as fetching and updating time entries, and logs errors when responses are unsuccessful.
    """
    def __init__(self, api_key: str, base_url: str, workspace_id: str):
        """
        Initializes the ClockifyService with required credentials.

        Args: 
            api_key (str): The Clockify API key for authenticating requests.
            base_url (str): The base URL of the Clockify API (e.g. 'https://api.clockify.me/api/v1').
            workspace_id (str): The Clockify workspace Id to be used in requests.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.workspace_id = workspace_id
    
    def _send_request(
            self, 
            method: str, 
            endpoint: str, 
            headers: Optional[Dict] = None, 
            params: Optional[Dict] = None, 
            json_data: Optional[Dict] = None
        ) -> Dict:
        """
        Send an HTTP request to the specified Clockify API endpoint.

        Args: 
            method (str): The HTTP method to use (e.g. 'GET', 'POST', 'PUT').
            endpoint (str): The API endpoint path (e.g. '/workspaces/...).
            headers (Optional[Dict], optional): Additional headers to include in the request. Defaults to None.
            params (Optional[Dict], optional): Query parameter to include in the request URL. Defaults to None.
            json_data (Optional[Dict], optional): Json payload for PUT method. Defaults to None.

        Returns:
            Dict: The JSON response from the Clockify API.

        Raises:
            frappe.ValidationError: If the API response status code is not 200 or 201.
        """

        if headers is None:
            headers = {}
        
        default_headers = {
            "X-API-Key": self.api_key
        }

        merged_headers = {**default_headers, **headers}

        api_url = f"{self.base_url}{endpoint}"

        response = requests.request(
            method=method,
            url=api_url,
            headers=merged_headers,
            params=params,
            json=json_data
        )

        if response.status_code not in (200, 201):
            frappe.log_error(
                title="Clockify API Request Error",
                message=(
                    f"Fehler beim Aufrufen der Clockify-API.\n"
                    f"URL: {api_url}\n"
                    f"Statuscode: {response.status_code}\n"
                    f"Response: {response.text}"
                )
            )
            frappe.throw(
                "Es gab einen Fehler bei der Kommunikation mit der Clockify-API. "
                "Bitte überprüfen Sie die Error Logs für weitere Details."
            )
        
        return response.json()


    def fetch_clockify_entries(self, user_id: str, tag_id: str, start_iso: str, end_iso: str) -> List[Dict]:
        """
        Fetch time entries for a given user ID, starting form a time picked by the user, and filters out all entries which are already imported.

        Args:
            user_id (str): The Clockify user ID whose entries should be fetched.
            tag_id (str): Id to know if entry has been imported
            start_iso (str): Start date and time for time entries import. 
            end_iso (str): End date and time for time entries import. 
        
        Returns:
            List[Dict]: A list of fetched time entries from Clockify.

        Raises:
            frappe.ValidationError: If the API call fails.
        """
        endpoint_url = f"/workspaces/{self.workspace_id}/user/{user_id}/time-entries"

        params = {
            "start": start_iso,
            "end": end_iso,   
            "hydrated": "true",
            "page": DEFAULT_PAGE_NUMBER,
            "page-size": MAX_PAGE_SIZE
        }

        entries = self._send_request(
            method="GET",
            endpoint=endpoint_url,
            params=params
        )
    
        filtered_entries = [
            entry for entry in entries
            if tag_id not in entry.get("tagIds", [])
        ]

        return filtered_entries

    def update_clockify_entry(self, entry_id: str, data: dict) -> None:
        """
        Update an existing Clockify time entry with new data.

        Args:
            entry_id (str): The ID of the Clockify entry to be updated.
            data (dict): A dictionary containing the update data for the time entry.

        Raises:
            frappe.ValidationError: If the API call fails.
        """
        endpoint_url = f"/workspaces/{self.workspace_id}/time-entries/{entry_id}"
        headers = {"Content-Type": "application/json"}

        self._send_request(
            method="PUT",
            endpoint=endpoint_url,
            headers=headers,
            json_data=data
        )