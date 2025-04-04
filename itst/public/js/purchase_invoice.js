frappe.ui.form.on('Purchase Invoice', {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
		    frm.add_custom_button(__("Projekt"), function() {
                frappe.prompt([
                    {'fieldname': 'project', 'fieldtype': 'Link', 'options': 'Project', 'label': __('Project'), 'reqd': 1}  
                ],
                function(values){
                    for (var i = 0; i < cur_frm.doc.items.length; i++) {
                        frappe.model.set_value(cur_frm.doc.items[i].doctype, cur_frm.doc.items[i].name, 'project', values.project);
                    }
                    frappe.show_alert(__("Updated"));
                },
                __('Project'),
                'OK'
                );
            });
		}
	}
});