// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt
// Common functions

function cache_email_footer() {
    try {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Signature",
                'name': frappe.session.user
            },
            'callback': function(response) {
                var signature = response.message;

                if (signature) {
                    locals.email_footer = signature.email_footer;
                } 
            }
        });
    } catch { 
        console.log("signature not found"); 
    }
}
