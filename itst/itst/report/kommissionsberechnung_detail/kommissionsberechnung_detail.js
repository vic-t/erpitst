// Copyright (c) 2022, libracore, ITST and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kommissionsberechnung Detail"] = {
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
        },
        {
            "fieldname":"item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "reqd": 1
        }
    ]
};
