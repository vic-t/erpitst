// Copyright (c) 2022, ITST, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["STP Lizenzumsatz"] = {
    "filters": [
        {
            "fieldname":"item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "default": "STP-Lizenzen"
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname":"to_date",
            "label": __("ToDate"),
            "fieldtype": "Date"
        }
    ]
};
