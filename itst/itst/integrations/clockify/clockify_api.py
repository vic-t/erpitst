import requests
import frappe

from .utilities import (
    get_week_start_iso
)

def fetch_clockify_entries(workspace_id, clockify_user_id, clockify_api_key, clockify_base_url):
    week_start_iso  = get_week_start_iso()
    endpoint_url = f"{clockify_base_url}/workspaces/{workspace_id}/user/{clockify_user_id}/time-entries"
    headers = {"X-Api-Key": clockify_api_key}

    params = {
        "get-week-before": week_start_iso ,   
        "hydrated": "true",
        "page": 1,
        "page-size": 5000
    }

    response = requests.get(endpoint_url, headers=headers, params=params)
    if response.status_code == 200:
        entries = response.json()
        return entries
    else:
        frappe.log_error(f"Fehler beim Abrufen der Einträge: {response.status_code}, {response.text}. Bitte überprüfen Sie Ihre API-Schlüssel und die Anfrageparameter.")
        frappe.throw("Fehler beim Abrufen der Einträge.")

def update_clockify_entry(workspace_id, entry, clockify_tags_id, clockify_api_key, clockify_base_url):
    endpoint_url = f"{clockify_base_url}/workspaces/{workspace_id}/time-entries/{entry['id']}"
    headers = {"X-Api-Key": clockify_api_key, "Content-Type": "application/json"}

    data = {
        "description": entry.get("description", "No description"),
        "end": entry["timeInterval"]["end"],
        "projectId": entry["projectId"],
        "start": entry["timeInterval"]["start"],
        "tagIds": [f"{clockify_tags_id}"],
    }

    response = requests.put(endpoint_url, headers=headers, json=data)
    if response.status_code != 200:
        frappe.log_error(f"Fehler beim Aktualisieren des Clockify-Eintrags nach dem Import: Die Aktualisierung des Eintrags mit der ID {entry['id']} ist fehlgeschlagen. HTTP-Statuscode: {response.status_code}, Serverantwort: {response.text}. Bitte überprüfen Sie die API-Schlüssel, den Eintrag oder die Verbindung zu Clockify.", "Clockify Update Fehler")
        frappe.throw(f" Der Clockify-Eintrag mit der ID {entry['id']} konnte nach dem Import nicht aktualisiert werden. Dies könnte auf einen API-Fehler oder ein Problem mit der Verbindung zu Clockify hinweisen. Bitte wenden Sie sich an den Administrator, um den Fehler zu beheben.")
