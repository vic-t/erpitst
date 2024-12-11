frappe.ui.form.on('Project', {
	refresh(frm) {
	    // display notes at the top
		if (frm.doc.notes) {
		    cur_frm.dashboard.add_comment( frm.doc.notes , 'green', true);
 
		    var elements = document.getElementsByClassName("green");
		    for (var i = 0; i < elements.length; i++) {
		        elements[i].style.setProperty('color', 'dimgray', 'important');
		    }
		}

        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"project": frm.doc.name});
        });
	}
});