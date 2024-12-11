frappe.ui.form.on('Task', {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Offene TS-Positionen"), function() {
                frappe.set_route("query-report", "Offene TS-Positionen", {"task": frm.doc.name});
            });

            frm.add_custom_button(__('Zugehörige Zammad-Tickets'), function() {
            	window.open("https://support.itst.ch/#search/" + frm.doc.name, '_blank').focus();
            }).addClass("btn-primary");
        }
    }
});

