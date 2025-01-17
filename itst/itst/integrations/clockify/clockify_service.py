import requests
import frappe
from typing import List, Dict, Optional

DEFAULT_PAGE_NUMBER = 1
MAX_PAGE_SIZE = 5000

class ClockifyService:
    def __init__(self, api_key: str, base_url: str, workspace_id: str):
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

        if headers is None:
            headers ={}
        
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


    def fetch_clockify_entries(self, user_id: str, week_start_iso: str) -> List[Dict]:
        endpoint_url = f"/workspaces/{self.workspace_id}/user/{user_id}/time-entries"

        params = {
            "get-week-before": week_start_iso ,   
            "hydrated": "true",
            "page": DEFAULT_PAGE_NUMBER,
            "page-size": MAX_PAGE_SIZE
        }

        return self._send_request(
            method="GET",
            endpoint=endpoint_url,
            params=params
        )

    def update_clockify_entry(self, entry_id: str, data: dict) -> None:
        endpoint_url = f"/workspaces/{self.workspace_id}/time-entries/{entry_id}"
        headers = {"Content-Type": "application/json"}

        self._send_request(
            method="PUT",
            endpoint=endpoint_url,
            headers=headers,
            json_data=data
        )