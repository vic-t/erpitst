# Copyright (c) 2022, libracore, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import date
from dateutil.relativedelta import relativedelta
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {'fieldname': 'description', 'label': _('Description'), 'fieldtype': 'Data', 'width': 200}, 
        {'fieldname': 'm1', 'label': date.today() + relativedelta(months=+1), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm2', 'label': date.today() + relativedelta(months=+2), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm3', 'label': date.today() + relativedelta(months=+3), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm4', 'label': date.today() + relativedelta(months=+4), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm5', 'label': date.today() + relativedelta(months=+5), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm6', 'label': date.today() + relativedelta(months=+6), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm7', 'label': date.today() + relativedelta(months=+7), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm8', 'label': date.today() + relativedelta(months=+8), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm9', 'label': date.today() + relativedelta(months=+9), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm10', 'label': date.today() + relativedelta(months=+10), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm11', 'label': date.today() + relativedelta(months=+11), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'm12', 'label': date.today() + relativedelta(months=+12), 'fieldtype': 'Currency', 'width': 100}
    ]
    
def get_data(filters):
    dates = [
        date.today(),
        date.today() + relativedelta(months=+1),
        date.today() + relativedelta(months=+2),
        date.today() + relativedelta(months=+3),
        date.today() + relativedelta(months=+4),
        date.today() + relativedelta(months=+5),
        date.today() + relativedelta(months=+6),
        date.today() + relativedelta(months=+7),
        date.today() + relativedelta(months=+8),
        date.today() + relativedelta(months=+9),
        date.today() + relativedelta(months=+10),
        date.today() + relativedelta(months=+11),
        date.today() + relativedelta(months=+12)
    ]
    data = []
    # opportunities
    _data = {
        'description': "Chancen"
    }
    for i in range(1,4):
        _data["m{0}".format(i)] = frappe.db.sql("""
            SELECT IFNULL(SUM(`opportunity_amount` * `probability` / 100), 0) AS `sum`
            FROM `tabOpportunity`
            WHERE `transaction_date` > "{from_date}" 
              AND `transaction_date` <= "{end_date}"
              AND `status` = "Open";
            """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
    data.append(_data)
    
    # quotations
    _data = {
        'description': "Angebote"
    }
    for i in range(1,7):
        _data["m{0}".format(i)] = frappe.db.sql("""
            SELECT IFNULL(SUM(`base_net_total` * 0.65), 0) AS `sum`
            FROM `tabQuotation`
            WHERE `valid_till` > "{from_date}" 
              AND `valid_till` <= "{end_date}"
              AND `docstatus` = 1
              AND `status` = "Open";
            """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
    data.append(_data)
    
    # sales orders
    _data = {
        'description': "Aufträge"
    }
    for i in range(1,7):
        _data["m{0}".format(i)] = frappe.db.sql("""
            SELECT IFNULL(SUM(`base_net_total` * 0.85), 0) AS `sum`
            FROM `tabSales Order`
            WHERE `delivery_date` > "{from_date}" 
              AND `delivery_date` <= "{end_date}"
              AND `docstatus` = 1;
            """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
    data.append(_data)
    
    # support
    _data = {
        'description': "Support"
    }
    last_average = frappe.db.sql("""
        SELECT IFNULL(SUM(`tabSales Invoice Item`.`base_net_amount`), 0) AS `sum`
        FROM `tabSales Invoice Item`
        LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
        WHERE `tabSales Invoice`.`posting_date` > "{from_date}" 
          AND `tabSales Invoice`.`posting_date` <= "{end_date}"
          AND `tabSales Invoice`.`docstatus` = 1
          AND `tabSales Invoice Item`.`item_code` = "IT-Support";
        """.format(from_date=date.today() + relativedelta(months=-3), end_date=date.today()), as_dict=True)[0]['sum']
    for i in range(1,7):
        _data["m{0}".format(i)] = 0.9 * (last_average / 3)
    data.append(_data)
    
    # add values from budget
    # TODO
    
    # revenue sums
    # support
    _data = {
        'description': "Einnahmen"
    }
    for i in range(1,13):
        total = 0
        key = "m{0}".format(i)
        for row in data:
            if key in row:
                total += row[key]
        _data[key] = total
    data.append(_data)
    
    return data
