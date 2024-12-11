frappe.ui.form.on('Contact', {
    before_save: function(frm) {
        if ((!frm.doc.letter_salutation) && (frm.doc.salutation) && (frm.doc.gender)) {
            if (frm.doc.gender === "Male") {
                cur_frm.set_value("letter_salutation", "Sehr geehrter " + frm.doc.salutation + " " + frm.doc.last_name);
            } else if (frm.doc.gender === "Female") {
                cur_frm.set_value("letter_salutation", "Sehr geehrte " + frm.doc.salutation + " " + frm.doc.last_name);
            }
        }
    }
});