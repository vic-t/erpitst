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
    ],
    "onload": (report) => {
        // add event listener for double clicks
        cur_page.container.addEventListener("dblclick", function(event) {
            if (event.delegatedTarget) {
                var row = event.delegatedTarget.getAttribute("data-row-index");
                var column = event.delegatedTarget.getAttribute("data-col-index");
                var content = null;
                if (event.delegatedTarget.innerText) {
                    content = event.delegatedTarget.innerText;
                }
                if (content === "...") {
                    var item_group = frappe.query_report.data[row].item_group;
                    var year = frappe.query_report.filters[0].value;
                    var month = frappe.query_report.filters[1].value;
                    var sales_partner = frappe.query_report.filters[2].value;
                    frappe.set_route("query-report", "Kommissionsberechnung Detail", 
                        {
                            "item_group": item_group,
                            "year": year,
                            "month": month,
                            "sales_partner": sales_partner
                        }
                    );
                }
            }
        });
    }
};
