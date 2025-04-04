frappe.ui.form.on('Gespraechsnotiz', {
	before_save(frm) {
		cur_frm.set_value("short_remarks", frm.doc.remarks.replace(/<\/?[^>]+(>|$)/g, "").substring(0, 140));
	}
});