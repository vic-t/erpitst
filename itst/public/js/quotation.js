frappe.ui.form.on('Quotation', {
	refresh(frm) {
		// your code here
	},
	on_submit(frm) {
	    frappe.call({
          'method': 'itst.itst.utils.create_combined_pdf',
          'args':{
            'dt': 'Quotation',
            'dn': frm.doc.name,
            'print_format': 'Offerte'
          },
            'callback': function(response) {
                cur_frm.reload_doc();
            }
        });
	},
	vorlage_eingangstext(frm) {
	    if (frm.doc.vorlage_eingangstext) {
	        frappe.call({
                'method': "frappe.client.get",
                'args': {
                    "doctype": "Terms and Conditions",
                    "name": frm.doc.vorlage_eingangstext
                },
                'callback': function(response) {
                    var vorlage = response.message;
                    if (vorlage) {
                       cur_frm.set_value("eingangstext", vorlage.terms);
                    } 
                }
            });
	    }
	}
});