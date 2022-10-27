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

frappe.ui.form.on('Abo Item', {
   item: function(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        if (d.item) {
            frappe.call({
                'method': "frappe.client.get_list",
                'args': {
                    'doctype': "Item Price",
                    'filters': [
                        ["item_code","=", d.item],
                        ["selling", "=", 1]
                    ],
                    'fields': ["price_list_rate"]
                },
                'callback': function(response) {
                    if ((response.message) && (response.message.length > 0)) {
                        frappe.model.set_value(cdt, cdn, "rate", response.message[0].price_list_rate);
                    }
                }
            });
        }
   } 
});
