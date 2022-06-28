# -*- coding: utf-8 -*-
# Copyright (c) 2022, ITST, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
from frappe import _
from datetime import datetime, timedelta

class Abo(Document):
    def create_invoice(self):
        sinv = frappe.get_doc({
            'doctype': 'Sales Invoice',
            'customer': self.customer,
        })
        contract_start = datetime.strptime(self.start_date, "%Y-%m-%d")
        start_date = datetime(datetime.now().year, contract_start.month, contract_start.day)
        end_date = start_date + timedelta(days=365)
        
        for i in self.items:
            default_description = frappe.get_value("Item", i.item, 'description')
            description = "{0}<br>{1}".format(default_description, 
                _("Periode: {0} - {1}").format(start_date.strftime("%d.%m.%Y"), end_date.strftime("%d.%m.%Y")))
            sinv.append('items', {
                'item_code': i.item,
                'qty': i.qty,
                'rate': i.rate,
                'description': description
            });
        
        # get default taxes
        default_taxes = frappe.get_all("Sales Taxes and Charges Template", filters={'is_default': 1}, fields=['name'])
        if len(default_taxes) == 0:
            frappe.throw( _("Please define a default sales taxes and charges template."), _("Configuration missing"))
        tax_template = frappe.get_doc("Sales Taxes and Charges Template", default_taxes[0]['name'])
        sinv.taxes_and_charges = tax_template.name
        sinv.taxes = tax_template.taxes
        # create invoice record
        sinv.insert(ignore_permissions=True)
        
        self.append('invoices', {
            'sales_invoice': sinv.name,
            'date': sinv.posting_date
        })
        self.save()
        return sinv.name
    pass

# this function will create invoices due today (e.g. start date was the same month/day
def create_todays_invoices():
    d = datetime.date.today()
    today = "-{:02d}-{:02d}".format(d.month, d.day)
    invoices = frappe.db.sql("""
        SELECT `name`
        FROM `tabAbo`
        WHERE SUBSTRING(`start_date`, 5, 6) = "{today}";""".format(today=today), as_dict=True)
    if invoices and len(invoices) > 0:
        for i in invoices:
            doc = frappe.get_doc("Abo", i['name'])
            doc.create_invoice()
    return
