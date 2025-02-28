// Copyright (c) 2024, ITST and contributors
// For license information, please see license.txt

frappe.ui.form.on('Clockify Import Settings', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Import now'), function() {
				frappe.call({
					method: "itst.itst.integrations.clockify_integration.test_connection",
					callback: function(response) {
                        console.log("Response from server:", response.message);
                    }
				});
			});
		}
	}
});
