frappe.ui.form.on('Item', {
    refresh(frm) {
        frm.add_custom_button(__("STP Lizenzumsatz"), function() {
            frappe.set_route("query-report", "STP Lizenzumsatz", {"item_group": frm.doc.item_group});
        });
    }
});
