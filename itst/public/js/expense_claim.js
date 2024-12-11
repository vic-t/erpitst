frappe.ui.form.on('Expense Claim', {
    on_submit: function (frm) {
        create_pretax_journal_entry(frm);
    },
    before_cancel: function (frm) {
        cancel_pretax_journal_entry(frm);  
    },
    before_save: function(frm) {
        total_pretax(frm);
    }
});
 
function total_pretax(frm) {
    var total_pretax = 0.0;
    for (var i = 0; i < frm.doc.expenses.length; i++) {
        total_pretax += frm.doc.expenses[i].vorsteuer;
    }
    cur_frm.set_value('total_pretax', total_pretax);
}
 
function create_pretax_journal_entry(frm) {
    frappe.call({
        method: 'erpnextswiss.erpnextswiss.expenses.expense_pretax_various',
        args: {
            expense_claim: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert("Vorsteuer angerechnet: " + r.message.name);
                cur_frm.reload_doc();
            } 
        }
    });
}
 
function cancel_pretax_journal_entry(frm) {
    if (frm.doc.pretax_record) {
        frappe.call({
            method: 'erpnextswiss.erpnextswiss.expenses.cancel_pretax',
            args: {
                expense_claim: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.show_alert("Vorsteuerdatensatz storniert. " + frm.doc.pretax_record);
                } 
            }
        });
    }
}