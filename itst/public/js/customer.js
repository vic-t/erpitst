// global
cur_frm.dashboard.add_transactions([
    {
        'label': 'Abo',
        'items': ['Abo']
    } 
]);

frappe.ui.form.on('Customer', {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Offene TS-Positionen"), function() {
                frappe.set_route("query-report", "Offene TS-Positionen", {"customer": frm.doc.name});
            });
        }
    }
});
