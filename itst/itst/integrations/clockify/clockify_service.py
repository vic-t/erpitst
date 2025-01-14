import requests
import frappe
from typing import List, Dict

class ClockifyService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def fetch_clockify_entries(self, workspace_id: str, user_id: str, week_start_iso: str) -> List[Dict]:
        endpoint_url = f"{self.base_url}/workspaces/{workspace_id}/user/{user_id}/time-entries"
        headers = {"X-Api-Key": self.api_key}

        params = {
            "get-week-before": week_start_iso ,   
            "hydrated": "true",
            "page": 1,
            "page-size": 5000
        }

        response = requests.get(endpoint_url, headers=headers, params=params)
        if response.status_code != 200:
            frappe.log_error(
                f"Fehler beim Abrufen der Einträge: {response.status_code}, {response.text}",
                "Clockify Fetch Error"
            )
            frappe.throw("Fehler beim Abrufen der Einträge von Clockify.")

        return response.json()

    def update_clockify_entry(self, workspace_id: str, entry_id: str, data: dict):
        endpoint_url = f"{self.base_url}/workspaces/{workspace_id}/time-entries/{entry_id}"
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

        response = requests.put(endpoint_url, headers=headers, json=data)
        if response.status_code != 200:
            frappe.log_error(f"Fehler beim Aktualisieren des Clockify-Eintrags nach dem Import: Die Aktualisierung des Eintrags mit der ID {entry_id} ist fehlgeschlagen. HTTP-Statuscode: {response.status_code}, Serverantwort: {response.text}. Bitte überprüfen Sie die API-Schlüssel, den Eintrag oder die Verbindung zu Clockify.", "Clockify Update Fehler")
            frappe.throw(f" Der Clockify-Eintrag mit der ID {entry_id} konnte nach dem Import nicht aktualisiert werden. Dies könnte auf einen API-Fehler oder ein Problem mit der Verbindung zu Clockify hinweisen. Bitte wenden Sie sich an den Administrator, um den Fehler zu beheben.")