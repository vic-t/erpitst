# Copyright (c) 2022, libracore, ITST, and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import calendar
import datetime

def execute(filters=None):
    columns, data = [], []
        
    # prepare data range
    first_last_day = calendar.monthrange(filters.year, filters.month)
    from_date = datetime.datetime(filters.year, filters.month, 1).date()
    to_date = datetime.datetime(filters.year, filters.month, first_last_day[1]).date()
        
    columns = [
        {'fieldname': 'date', 'label': _('Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'sales_invoice', 'label': _('Sales Invoice'), 'fieldtype': 'Link', 'options': 'Sales Invoice', 'width': 100}, 
        {'fieldname': 'amount', 'label': _('Amount'), 'fieldtype': 'Currency', 'width': 100}
    ]
    
    sql_query = """SELECT
            `tabSales Invoice`.`posting_date` AS `date`,
            `tabSales Invoice`.`name` AS `sales_invoice`,
            IFNULL(SUM(`tabSales Invoice Item`.`base_net_amount`), 0) AS `amount`
        FROM `tabSales Invoice Item`
        LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
        WHERE
            `tabSales Invoice`.`docstatus` = 1 
            AND `tabSales Invoice`.`posting_date` >= "{from_date}"
            AND `tabSales Invoice`.`posting_date` <= "{to_date}"
            AND `tabSales Invoice`.`sales_partner` = "{sales_partner}"
            AND `tabSales Invoice Item`.`item_group` = "{item_group}"
        ;""".format(
            from_date=from_date, to_date=to_date, sales_partner=filters.sales_partner, 
            item_group=filters.item_group)
    data = frappe.db.sql(sql_query, as_dict = True)

    return columns, data
