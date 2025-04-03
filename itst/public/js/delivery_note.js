frappe.ui.form.on('Delivery Note', {
    on_submit(frm) {
        frappe.call({
            'method': "itst.itst.utils.set_batch_customer",
            'args': {
                'delivery_note': frm.doc.name
            }
        });
        
        check_create_accrual(frm, ['WJ-Liz'], '3300 - STP Lizenzerlös - ITST', '2230 - KK STP - ITST');
    },

	after_cancel(frm) {
	    cancel_accrual(frm);
	}
});
 
function check_create_accrual(frm, items, debit, credit) {
    var accrual_ratio = 0.6;        // 60%
    var accrual_amount = 0;
    // get amount
    (frm.doc.items || []).forEach(function (item) {
        if (items.includes(item.item_code)) {
            accrual_amount += (item.base_net_amount * accrual_ratio);
        }
    });
    if (accrual_amount > 0) {
        frappe.call({
           'method': "itst.itst.utils.create_accrual_jv",
           'args': {
                'amount': accrual_amount,
                'debit_account': debit,
                'credit_account': credit,
                'date': frm.doc.posting_date,
                'remarks': 'Rückstellung zu Rechnung ' + frm.doc.name,
                'document': frm.doc.name
           },
           callback: function(response) {
                frappe.show_alert( __("Buchungssatz für Rückstellung erstellt: <a href='/desk#Form/Journal Entry/" + 
                    response.message + "'>" + response.message + "</a>"));
           }
        });
    }
}
 
function cancel_accrual(frm) {
    frappe.call({
       'method': "itst.itst.utils.cancel_accrual_jv",
       'args': {
            'date': frm.doc.posting_date,
            'document': frm.doc.name
       },
       callback: function(response) {
            frappe.show_alert( __("Buchungssatz für Rückstellung storniert: <a href='/desk#Form/Journal Entry/" + 
                response.message + "'>" + response.message + "</a>"));
       }
    });
}