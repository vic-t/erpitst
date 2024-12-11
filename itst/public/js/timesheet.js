frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Offene TS-Positionen"), function() {
            frappe.set_route("query-report", "Offene TS-Positionen", {"employee": frm.doc.employee});
        });
    }
});

frappe.ui.form.on('Timesheet Detail', {
    duration(frm, cdt, cdn) {
        var duration_h = get_hrs_from_duration(frappe.model.get_value(cdt, cdn, 'duration'));
        frappe.model.set_value(cdt, cdn, 'hours', duration_h);
    },
    billing_duration(frm, cdt, cdn) {
        var duration_h = get_hrs_from_duration(frappe.model.get_value(cdt, cdn, 'billing_duration'));
        frappe.model.set_value(cdt, cdn, 'billing_hours', duration_h);
    }
});

function get_hrs_from_duration(duration) {
    var duration_h = null;
    if (duration) {
        var str_parts = duration.split(":");
        var duration_min = parseInt(str_parts[0]) * 60 + parseInt(str_parts[1]);
        duration_h = duration_min/60;
    }
    return duration_h;
}

// this mapping table defines which item is used for a activity type - kategorie combination
var mapping_table = {
    'Support': {
        'WinJur': 'WinJur-Support',
        'DMS': 'DMS-Support',
        'Informatik': 'IT-Arbeiten',
        'Telefonie': 'IT-Arbeiten',
        'Web': 'IT-Arbeiten'
    },
    'Projektarbeit': {
        'WinJur': 'WinJur-Support',
        'DMS': 'DMS-Support',
        'Informatik' : 'IT-Arbeiten',
        'Telefonie': 'IT-Arbeiten',
        'Web': 'IT-Arbeiten'
    }
};
 
frappe.ui.form.on('Timesheet', {
	refresh(frm) {
		// category filters
		frm.fields_dict.time_logs.grid.get_field('category').get_query =
            function(doc, cdt, cdn) {
            	return {
            	    query: "itst.itst.filters.activity_item",
                    filters: {
            		    "keyword":  "Dienstleistungen",
            		    "activity_type": locals[cdt][cdn].activity_type
                    }
        	    };
            };
        // set project filters
        frm.fields_dict.time_logs.grid.get_field('project').get_query =   
            function() {                                                                      
            	return {
                    filters: {
            		    "is_active": "Yes"
            	    }
            	};
            };
 
        // break button
        frm.add_custom_button(__("Pause"), function() {
            add_break(frm);
        });
	},
	before_save(frm) {
	    // loop throught time logs and check if billable rows have a category
	    for (var i = 0; i < frm.doc.time_logs.length; i++) {
	        if ((frm.doc.time_logs[i].billable === 1) && (!frm.doc.time_logs[i].category)) {
	            frappe.msgprint( "Bitte in Zeile " + (i + 1) + " einen Artikel wählen.", __("Daten prüfen") );
	        }
	    }
	},
	before_submit(frm) {
	    // loop throught time logs and check if billable rows have a category
	    for (var i = 0; i < frm.doc.time_logs.length; i++) {
	        if ((frm.doc.time_logs[i].billable === 1) && (!frm.doc.time_logs[i].category)) {
	            frappe.msgprint( "Bitte in Zeile " + (i + 1) + " einen Artikel wählen.", __("Buchung fehlgeschlagen") );
	            frappe.validated=false;
	        }
	    }
	}
});
 
frappe.ui.form.on('Timesheet Detail', {
    time_logs_add(frm, cdt, cdn) {
        /* this is a hotfix to clear project and task in new rows */
        frappe.model.set_value(cdt, cdn, "project", null);
        frappe.model.set_value(cdt, cdn, "task", null);
 
        var row_idx = frappe.model.get_value(cdt, cdn, 'idx');
        if (row_idx > 1) {
            var last_time = frm.doc.time_logs[row_idx - 2].to_time;
            if (last_time) {
                frappe.model.set_value(cdt, cdn, 'from_time', last_time);
            }
        }
    },
    zammad_ticket(frm, cdt, cdn) {
        show_zammad_link(frm, cdt, cdn);
    },
	form_render(frm, cdt, cdn) {
		show_zammad_link(frm, cdt, cdn);
    },
    hours(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'billing_hours', frappe.model.get_value(cdt, cdn, 'hours'));
        frappe.model.set_value(cdt, cdn, 'billing_duration', frappe.model.get_value(cdt, cdn, 'duration'));
    },
    activity_type(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (["Projektarbeit", "Support", "Fahrtzeit"].includes(row.activity_type)) {
            frappe.model.set_value(cdt, cdn, 'billable', 1);
        }
    },
    kategorie(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if ((row.activity_type) && (row.kategorie)) {
            frappe.model.set_value(cdt, cdn, 'category', mapping_table[row.activity_type][row.kategorie]);
        }
    },
    aktivitaet(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'activity_type', locals[cdt][cdn].aktivitaet);
    }
});
 
function show_zammad_link(frm, cdt, cdn) {
    var child = locals[cdt][cdn];
	if (child.zammad_ticket) {
    	var wrapper = frm.fields_dict[child.parentfield].grid.grid_rows_by_docname[cdn].grid_form.fields_dict['zammad_link_html'].wrapper;
		$(wrapper).empty();
		$('<a href="' + child.zammad_ticket + '" target="_blank">Ticket öffnen</a>').appendTo(wrapper);
    }
}
 
function add_break(frm) {
    if (frm.doc.time_logs.length >= 1) {
        frappe.prompt([
                {'fieldname': 'duration', 'fieldtype': 'Select', 'label': 'Dauer', 'options': '0:05\n0:10\n0:15\n0:20\n0:25\n0:30\n0:35\n0:40\n0:45\n0:50\n0:55\n1:00\n1:05\n1:10\n1:15\n1:20\n1:25\n1:30\n1:35\n1:40\n1:45\n1:50\n1:55\n2:00\n2:05\n2:10\n2:15\n2:20\n2:25\n2:30\n2:35\n2:40\n2:45\n2:50\n2:55\n3:00\n3:05\n3:10\n3:15\n3:20\n3:25\n3:30\n3:35\n3:40\n3:45\n3:50\n3:55\n4:00', 'reqd': 1}  
            ],
            function(values){
                var last_time = new Date(frm.doc.time_logs[frm.doc.time_logs.length - 1].to_time);
                var duration_h = null;
                if (values.duration) {
                    var str_parts = values.duration.split(":");
                    var duration_min = parseInt(str_parts[0]) * 60 + parseInt(str_parts[1]);
                    duration_h = duration_min/60;
                }
                console.log(duration_h);
                if (duration_h) {
                    var next_start = addHours(duration_h, last_time).toLocaleString( 'sv');
                    var child = cur_frm.add_child('time_logs');
                    frappe.model.set_value(child.doctype, child.name, 'from_time', next_start);
                    cur_frm.refresh_fields();
                }
            },
            'Pause',
            'OK'
        );
    }
}
 
function addHours(numOfHours, date = new Date()) {
  date.setTime(date.getTime() + numOfHours * 60 * 60 * 1000);
 
  return date;
}
