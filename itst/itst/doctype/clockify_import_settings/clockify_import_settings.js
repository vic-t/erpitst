// Copyright (c) 2024, ITST and contributors
// For license information, please see license.txt

frappe.ui.form.on('Clockify Import Settings', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Import now'), function() {
				const user_options = frm.doc.user_mapping.map(u => {
                    return {label: u.erpnext_employee_name, value: u.erpnext_employee};
                });

				if (user_options.length === 0) {
                    frappe.msgprint("No user mappings found.");
                    return;
                }

				frappe.prompt([
					{
						fieldname: 'selected_user_mapping',
						fieldtype: 'Select',
						label: 'Select Clockify User',
						options: user_options,
						reqd: 1
					}
				], function(values){
                    frappe.call({
                        method: "itst.itst.integrations.clockify_integration.run_clockify_import",
                        args: {
                            user_mapping_name: values.selected_user_mapping
                        },
                        callback: function(r) {
                            // Optional: Erfolgsmeldung anzeigen, aber die wird auch serverseitig ausgegeben
                        }
                    });
					console.log(values.selected_user_mapping)
                }, __('Select User to Import'), __('Import'));
			});
		}
	}
});
