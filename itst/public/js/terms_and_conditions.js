frappe.ui.form.on('Terms and Conditions', {
	html_raw(frm) {
	    if (!locals.is_internal_html) {
	        cur_frm.set_value("terms", frm.doc.html_raw);
	    } else {
	        locals.is_internal_html = false;
	    }
	},
	refresh(frm) {
	    cur_frm.set_value("html_raw", frm.doc.terms);
	    locals.is_internal_html = true;
	}
});