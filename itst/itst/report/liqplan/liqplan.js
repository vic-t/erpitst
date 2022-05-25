// Copyright (c) 2022, libracore, ITST and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Liqplan"] = {
    "filters": [

    ]
};

/* add event listener for double clicks to move up */
cur_page.container.addEventListener("dblclick", function(event) {
    var row = event.delegatedTarget.getAttribute("data-row-index");
    var column = event.delegatedTarget.getAttribute("data-col-index");
    //console.log("Row " + row + " column: " + column);
    frappe.call({
        'method': "itst.itst.report.liqplan.liqplan.show_details",
        "args": {
            "row": row,
            "column": column
        }
    });
});
