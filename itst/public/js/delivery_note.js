frappe.ui.form.on('Delivery Note', {
    on_submit(frm) {
        frappe.call({
            'method': "itst.itst.utils.set_batch_customer",
            'args': {
                'delivery_note': frm.doc.name
            }
        });
    }
});
