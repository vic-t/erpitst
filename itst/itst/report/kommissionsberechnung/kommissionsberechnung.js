// Copyright (c) 2022, ITST, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kommissionsberechnung"] = {
    "filters": [
        {
            "fieldname":"year",
            "label": __("Year"),
            "fieldtype": "Int",
            "default": new Date().getFullYear(),
            "reqd": 1
        },
        {
            "fieldname":"month",
            "label": __("Month"),
            "fieldtype": "Int",
            "default": new Date().getMonth() + 1,
            "reqd": 1
        },
        {
            "fieldname":"sales_partner",
            "label": __("Sales Partner"),
            "fieldtype": "Link",
            "options": "Sales Partner",
            "reqd": 1
        }
    ]
};
