frappe.ui.form.on('Project', {
    refresh(frm) {
        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"project": frm.doc.name});
        });
    }
});
