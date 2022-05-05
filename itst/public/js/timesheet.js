frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"employee": frm.doc.employee});
        });
    }
});

frappe.ui.form.on('Timesheet Detail', {
    duration(frm, cdt, cdn) {
        var duration_str = frappe.model.get_value(cdt, cdn, 'duration');
        if (duration_str) {
            var str_parts = duration_str.split(":")
            var duration_min = parseInt(str_parts[0]) * 60 + parseInt(str_parts[1]);
            var duration_h = duration_min/60;
            frappe.model.set_value(cdt, cdn, 'hours', duration_h);
        }
    }
});
