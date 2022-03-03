// Copyright (c) 2022, ITST, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Abo', {
    refresh: function(frm) {
        if (!cur_frm.__is_local) {
            frm.add_custom_button(__("Rechnung erstellen"), function() {
                frappe.call({
                    'method': 'create_invoice',
                    'doc': frm.doc,
                    'callback': function(response) {
                        frappe.show_alert( __("Rechnung erstellt: <a href='/desk#Form/Sales Invoice/" + 
                        response.message + "'>" + response.message + "</a>"));
                        cur_frm.reload_doc();
                    }
                });
            });
        }
    }
});
