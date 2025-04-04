// Copyright (c) 2024, ITST and contributors
// For license information, please see license.txt

frappe.ui.form.on('Clockify Import Settings', {
	refresh: function(frm) {

	  if (!frm.is_new()) {
		frm.add_custom_button(__('Import now'), function() {
  
		  const user_options = (frm.doc.user_mapping || []).map(u => {
			return {
			  label: u.erpnext_employee_name,
			  value: u.erpnext_employee
			};
		  });
		  if (user_options.length === 0) {
			frappe.msgprint("No user mappings found.");
			return;
		  } 
		  frappe.prompt([
			{
			  fieldname: 'selected_user_mapping',
			  fieldtype: 'Select',
			  label: 'Mitarbeiter Auswählen',
			  options: user_options,  
			  reqd: 1,
			  default: ""
			},
			{
			  fieldname: 'start_time',
			  fieldtype: 'Datetime',
			  label: 'Import Start Datum', 
			  reqd: 1
			},
			{
			  fieldname: 'end_time',
			  fieldtype: 'Datetime',
			  label: 'Import End Datum', 
			  reqd: 1
			}
		  ],
		  function(values) {
			frappe.call({
			  method: "itst.itst.integrations.clockify.run_clockify_import.run_clockify_import",
			  args: {
				user_mapping_name: values.selected_user_mapping,
				clockify_start_time: values.start_time,
				clockify_end_time: values.end_time
			  },
			  callback: function(r) {
				// optional: Rückmeldung an den Nutzer
			  }
			});
  
			console.log("Selected user: " + values.selected_user_mapping);
		  },
		  __('Import Auswahl'),
		  __('Import'));
		});
	  }
	}
});