frappe.ui.form.on('Sales Invoice', {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
    	    frm.add_custom_button(__("Timesheets abrechnen"), function() {
                if (frm.doc.customer) {
                    add_timesheet_positions(frm);
                } else {
                    frappe.msgprint("Bitte einen Kunden wählen");
                }
            });
 
            // override target email
            override_email(frm);
    	}
    	if ((frm.doc.__islocal) && (frm.doc.project) && (!frm.doc.customer)) {
    	    // fetch customer from project
    	    frappe.call({
                "method": "frappe.client.get",
                "args": {
                    "doctype": "Project",
                    "name": frm.doc.project
                },
                "callback": function(response) {
                    var project = response.message;
                    if (project.customer) {
                        cur_frm.set_value("customer", project.customer);
                        setTimeout(function () {
                            cur_frm.set_value("taxes_and_charges", "MWST (302) - ITST");
                        }, 1000);
                    } 
                }
            });
    	}
    	// custom mail dialog
    	if (frm.doc.docstatus === 1) {
    	     cur_frm.page.add_action_icon(__("fa fa-envelope-o"), function() {
                custom_mail_dialog(frm);
            });
    	}
    	// remove core email function
    	if (document.getElementsByClassName("fa-envelope-o").length === 0) {
            $("span[data-label='E-Mail']").parent().parent().remove();   // remove Menu > Email
        }
        cache_email_footer();       // prepare footer signature
	},
	before_save(frm) {
	    if (frm.doc.__islocal) {
            if (frm.doc.is_return === 1) {
                cur_frm.set_value("naming_series", "GU-.#####");
            }
        }
	},
	customer(frm) {
	    // hack: after changing the customer, hard-set taxes
	    setTimeout(function () {
            cur_frm.set_value("taxes_and_charges", "MWST (302) - ITST");
        }, 5000);
	}
});
 
function add_timesheet_positions(frm) {
    // get projects for this customer
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
 	    doctype: 'Project',
 	    filters: [
 	        ['customer', '=', frm.doc.customer]
 	    ],
        fields: ['name'],
      },
      callback: function(response) {
        var projects = [];
        var project = null;
        if (response.message.length > 0) { 
            for (var i = 0; i < response.message.length; i++) {
                projects.push(response.message[i].name);
            }
            project = projects[0];
        }
        // show dialog for timespan
        var now = new Date();
        var from_date = new Date(now.getFullYear() - 1, 11, 1);
        var to_date = new Date(now.getFullYear() - 1, 11, 31); 
        if (now.getMonth() > 0) {
            from_date = new Date(now.getFullYear(), (now.getMonth() - 1), 1);
            to_date = new Date(now.getFullYear(), now.getMonth(), 0);
        } 
        frappe.prompt([
                {'fieldname': 'from_date', 'fieldtype': 'Date', 'label': "Von Datum", 'reqd': 1, 'default': from_date},
                {'fieldname': 'to_date', 'fieldtype': 'Date', 'label': "Bis Datum", 'reqd': 1, 'default': to_date},
                {'fieldname': 'project', 'fieldtype': 'Select', 'label': "Projekt", 'reqd': 1, 'options': projects, 'default': project},
                {'fieldname': 'show_effective_hrs', 'fieldtype': 'Check', 'label': "Nicht verrechnete Stunden anzeigen", 'default': 0}
            ],
            function(values){
                // get all timesheets
                console.log("fetch times...");
                frappe.call({
                    method: 'itst.itst.utils.get_invoiceable_timesheets',
                    args: {
                 	    'project': values.project,
                 	    'from_date': values.from_date,
                 	    'to_date': values.to_date
                    },
                    //async: false,
                    callback: function(response) {
                        var timesheets = response.message; 
                        //console.log(timesheets);
                        var details = [];
                        for (var i = 0; i < timesheets.length; i++) {
                            // create item position
                            var child = cur_frm.add_child('items');
                            //console.log("Resultat get_employee_from_timesheet: " + get_employee_from_timesheet(timesheets[i].timesheet));
                            // Folgende Zeile wird asynchron durchgeführt. Lässt sich nicht einrichten scheinbar.
                            //frappe.db.get_doc('Timesheet', timesheets[i].timesheet).then(doc =>  console.log("Resultat DB-Direct: " + doc.employee_name));
                            frappe.db.get_value('Timesheet', timesheets[i].timesheet, 'employee_name').then(r => console.log("db.get_value: " + r.message.employee_name));
                            console.log("timesheet im loop: " + timesheets[i].timesheet);
                            frappe.model.set_value(child.doctype, child.name, 'item_code', timesheets[i].category || timesheets[i].activity_type);
                            frappe.model.set_value(child.doctype, child.name, 'timesheet', timesheets[i].timesheet);
                            frappe.model.set_value(child.doctype, child.name, 'ts_detail', timesheets[i].ts_detail);
                            var description = timesheets[i].from_time.substring(0, 10) + ": " +  timesheets[i].remarks;
                            if ((values.show_effective_hrs === 1) && ((timesheets[i].hours || 0) > timesheets[i].billing_hours)) {
                                description += "<br>Effektive Stunden: " + timesheets[i].hours;
                            }
                            details.push({'dt': child.doctype, 'dn': child.name, 'qty': timesheets[i].billing_hours, 'description': description});
                        }
                        cur_frm.refresh_field('items');
                        // wait for all item fields to be set before populating description
                        setTimeout(function () {
                            for (var i = 0; i < details.length; i++) {
                                frappe.model.set_value(details[i].dt, details[i].dn, 'description', details[i].description);
                                frappe.model.set_value(details[i].dt, details[i].dn, 'qty', details[i].qty);
                            }
                            cur_frm.refresh_field('items');
                        }, 1000);
                    }
                });
            },
            'Zeitraum',
            'OK'
        );
      }
    });
}
 
function override_email(frm) {
    if (frm.doc.customer) {
           frappe.call({
            "method": "frappe.client.get",
            "args": {
                "doctype": "Customer",
                "name": frm.doc.customer
            },
            "callback": function(response) {
                var customer = response.message;
                if (customer.rechnung_an) {
                    cur_frm.set_value("contact_person", customer.rechnung_an);
                } 
            }
        });
    }
}
 
function custom_mail_dialog(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Customer",
            "name": frm.doc.customer
        },
        "callback": function(response) {
            var customer = response.message;
            var recipient = frm.doc.email || frm.doc.email_id || frm.doc.contact_email;
            var cc = "";
            new frappe.views.CommunicationComposer({
    			doc: {
    			    doctype: frm.doc.doctype,
    			    name: frm.doc.name
    			},
    			subject: "Rechnung " + frm.doc.name,
    			recipients: recipient,
    			cc: cc,
    			attach_document_print: 1,
    			message: get_email_body()
    		});
        }
    });
}
 
function get_email_body() {
    return "<div><span style=\"/*color: rgb(31, 73, 125);*/\">Sehr geehrte Damen und Herren</span></div>"
    + "<div><br></div><div><span style=\"/*color: rgb(31, 73, 125);*/\">Als Beilage erhalten Sie unsere Rechnung.</span></div>"
    + "<div<br><br></div>"
    + "<div><br></div><div><span style=\"/*color: rgb(31, 73, 125);*/\">Freundliche Grüsse</span></div></div>"
    + "<div<br></div>"
    + (locals.email_footer || "");
}
 
function get_employee_from_timesheet(strTimeSheet) {
    var strTS = strTimeSheet;
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Timesheet",
            "name": strTS
        },
        async: false,
        "callback": function(response) {
           var timesheet = response.message;
 
            strTS = timesheet.employee_name;
            console.log("Berechneter Wert: " + strTS);
 
            } 
 
        });
    //setTimeout(() => {  console.log("Timeout over!"); }, 5000);    
    console.log("Rückgabewert: " + strTS);
    return strTS;
}