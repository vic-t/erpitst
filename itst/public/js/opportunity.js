frappe.ui.form.on('Opportunity', {
    sales_stage(frm) {
		if (frm.doc.sales_stage.startsWith("1")) {
		    cur_frm.set_value("probability", 10);
		} else if (frm.doc.sales_stage.startsWith("2")) {
		    cur_frm.set_value("probability", 20);
		} else if (frm.doc.sales_stage.startsWith("3")) {
		    cur_frm.set_value("probability", 30);
		} else if (frm.doc.sales_stage.startsWith("4")) {
		    cur_frm.set_value("probability", 50);
		} else if (frm.doc.sales_stage.startsWith("5")) {
		    cur_frm.set_value("probability", 65);
		} else if (frm.doc.sales_stage.startsWith("6")) {
		    cur_frm.set_value("probability", 80);
		} else if (frm.doc.sales_stage.startsWith("7")) {
		    cur_frm.set_value("probability", 0);
		}
	},
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