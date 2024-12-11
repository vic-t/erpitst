frappe.ui.form.on('Payment Entry', {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Löhne"), function() {
                deduct_to_salary(frm);
            }, __("Ausbuchen"));
            frm.add_custom_button(__("Spesen des Geldverkehrs"), function() {
                deduct_to_exchange(frm);
            }, __("Ausbuchen"));
        }
	}
});
 
function deduct_to_salary(frm) {
    add_deduction("1099 - Lohndurchlaufskonto - ITST", "Main - ITST", frm.doc.unallocated_amount || frm.doc.difference_amount);
}
 
function deduct_to_exchange(frm) {
    add_deduction("6900 - Finanzaufwand - ITST", "Main - ITST", frm.doc.unallocated_amount || frm.doc.difference_amount);
}