frappe.ui.form.on("Address", {
    pincode: function(frm) {
        if (frm.doc.pincode) {
	        get_city_from_pincode(frm.doc.pincode, 'city');
        }
    }
}); 