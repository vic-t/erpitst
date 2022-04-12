frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"employee": frm.doc.employee});
        });
    }
});
