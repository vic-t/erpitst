// Copyright (c) 2022, ITST, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Offene TS-Positionen"] = {
    "filters": [
        {
            "fieldname":"project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project"
        },
        {
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname":"employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        },
        {
            "fieldname":"show_all",
            "label": __("Alle Projekte anzeigen"),
            "fieldtype": "Check",
            "default": 0
        },
        {
            "fieldname":"show_invoiced",
            "label": __("Auch verrechnete anzeigen"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    "initial_depth": 0
};
