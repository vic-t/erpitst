frappe.ui.form.on('Lead', {
    zammad_ticket(frm) {
        show_zammad_link(frm);
    },
	refresh(frm) {
		show_zammad_link(frm);
    }
});
 
function show_zammad_link(frm) {
	if (frm.doc.zammad_ticket) {
    	var wrapper = cur_frm.fields_dict.zammad_link_html.wrapper;
		$(wrapper).empty();
		$('<a href="' + frm.doc.zammad_ticket + '" target="_blank">Ticket öffnen</a>').appendTo(wrapper);
    }
}