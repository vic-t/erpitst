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
  
		  frappe.call({
			method: 'frappe.client.get_list',
			args: {
			  doctype: 'Activity Type',
			  filters: {
				disabled: 0  
			  },
			  fields: ['name as value', 'activity_type as label'],
			  order_by: 'activity_type ASC',
			  limit_page_length: 100  
			},
			callback: function(r) {
			  let activity_type_options = r.message || [];
			  if (!activity_type_options.length) {
				frappe.msgprint("No active activity types found.");
				return;
			  }
  
			  frappe.call({
				method: 'frappe.client.get_list',
				args: {
				  doctype: 'Item',
				  filters: {
					disabled: 0
				  },
				  fields: ['item_code as value', 'item_name as label'],
				  order_by: 'item_name ASC',
				  limit_page_length: 100
				},
				callback: function(r2) {
				  let dienstleistungs_artikel_options = r2.message || [];
				  if (!dienstleistungs_artikel_options.length) {
					frappe.msgprint("No Dienstleistungsartikel found.");
					return;
				  }
  
				  frappe.prompt([
					{
					  fieldname: 'selected_user_mapping',
					  fieldtype: 'Select',
					  label: 'Select Clockify User',
					  options: user_options,  
					  reqd: 1
					},
					{
					  fieldname: 'activity_type',
					  fieldtype: 'Select',
					  label: 'Activity Type',
					  options: activity_type_options,  
					  reqd: 1
					},
					{
						fieldname: 'selected_user_mapping',
						fieldtype: 'Select',
						label: 'Select Clockify User',
						options: user_options,
						reqd: 1
					}

				  ],
				  function(values) {
					frappe.call({
					  method: "itst.itst.integrations.clockify_integration.run_clockify_import",
					  args: {
						user_mapping_name: values.selected_user_mapping,
						activity_type: values.activity_type,
						dienstleistungs_artikel: values.dienstleistungs_artikel
					  },
					  callback: function(r) {
					  }
					});
  
					console.log("Selected user: " + values.selected_user_mapping);
					console.log("Activity type: " + values.activity_type);
					console.log("Dienstleistungsartikel: " + values.dienstleistungs_artikel);
				  },
				  __('Select User to Import'),
				  __('Import'));
				  print(dienstleistungs_artikel)
				}
			  });
			}
		  });
		});
	  }
	}
});