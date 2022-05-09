frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"employee": frm.doc.employee});
        });
    }
});

frappe.ui.form.on('Timesheet Detail', {
    duration(frm, cdt, cdn) {
        var duration_h = get_hrs_from_duration(frappe.model.get_value(cdt, cdn, 'duration'));
        frappe.model.set_value(cdt, cdn, 'hours', duration_h);
    },
    billing_duration(frm, cdt, cdn) {
        var duration_h = get_hrs_from_duration(frappe.model.get_value(cdt, cdn, 'billing_duration'));
        frappe.model.set_value(cdt, cdn, 'billing_hours', duration_h);
    }
});

function get_hrs_from_duration(duration) {
    var duration_h = null;
    if (duration) {
        var str_parts = duration.split(":")
        var duration_min = parseInt(str_parts[0]) * 60 + parseInt(str_parts[1]);
        duration_h = duration_min/60;
    }
    return duration_h;
}
