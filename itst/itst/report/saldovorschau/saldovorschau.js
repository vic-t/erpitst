// Copyright (c) 2022, libracore, ITST and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Saldovorschau"] = {
    "filters": [
        {
            "fieldname":"account",
            "label": __("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "reqd": 1
        },
    ]
};
