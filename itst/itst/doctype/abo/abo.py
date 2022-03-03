# -*- coding: utf-8 -*-
# Copyright (c) 2022, ITST, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime

class Abo(Document):
    def create_invoice(self):
        sinv = frappe.get_doc({
            'doctype': 'Sales Invoice',
            'customer': self.customer,
        })
        for i in self.items:
            sinv.append('items', {
                'item_code': i.item,
                'qty': i.qty,
                'rate': i.rate
            });
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
