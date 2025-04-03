frappe.ui.form.on('Sales Partner', {
	refresh(frm) {
		frm.add_custom_button(__("Kommissionsabrechnung"), function() {
            frappe.set_route("query-report", "Kommissionsberechnung", {'sales_partner': frm.doc.name});
        });
	}
});