// global
cur_frm.dashboard.add_transactions([
    {
        'label': 'Abo',
        'items': ['Abo']
    },
    {
        'label': 'Lizenzen',
        'items': ['Batch']
    }  
]);

frappe.ui.form.on('Customer', {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Offene TS-Positionen"), function() {
                frappe.set_route("query-report", "Offene TS-Positionen", {"customer": frm.doc.name});
            });
        }
    }
});


frappe.ui.form.on('Customer Stakeholder', {
	contact(frm, cdt, cdn) {
		frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Contact",
                'name': frappe.model.get_value(cdt, cdn, 'contact')
            },
            'callback': function(response) {
                var contact = response.message;
 
                if (contact) {
                    frappe.model.set_value(cdt, cdn, 'email', contact.email_id);
                    frappe.model.set_value(cdt, cdn, 'phone', contact.phone);
                } 
            }
        });
 
	}
});