# Copyright (c) 2022, libracore, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date

def execute(filters=None):
    columns, data = [], []
            
    columns = get_columns()
    
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'date', 'label': _('Date'), 'fieldtype': 'Date', 'width': 80},
        {'fieldname': 'document', 'label': _('Document'), 'fieldtype': 'Dynamic Link', 'options': 'doctype', 'width': 100},
        {'fieldname': 'amount', 'label': _('Amount'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'balance', 'label': _('Balance'), 'fieldtype': 'Currency', 'width': 100}
    ]
    
def get_data(filters):
    sql_query = """
        SELECT
            *
        FROM
            (SELECT 
                `tabSales Invoice`.`posting_date` AS `date`,
                "Sales Invoice" AS `doctype`,
                `tabSales Invoice`.`name` AS `document`,
                `tabSales Invoice`.`outstanding_amount` AS `amount`,
                `tabSales Invoice`.`docstatus` AS `docstatus`
            FROM `tabSales Invoice`
            WHERE `tabSales Invoice`.`docstatus` < 2
              AND `tabSales Invoice`.`outstanding_amount` > 0
            UNION SELECT
                `tabPurchase Invoice`.`posting_date` AS `date`,
                "Purchase Invoice" AS `doctype`,
                `tabPurchase Invoice`.`name` AS `document`,
                (-1) * `tabPurchase Invoice`.`outstanding_amount` AS `amount` ,
                `tabPurchase Invoice`.`docstatus` AS `docstatus`
            FROM `tabPurchase Invoice`
            WHERE `tabPurchase Invoice`.`docstatus` = 1
              AND `tabPurchase Invoice`.`outstanding_amount` > 0
            ) AS `raw`
        ORDER BY `raw`.`date` ASC;"""
    transactions = frappe.db.sql(sql_query, as_dict=True)
    
    balance = frappe.db.sql("""
        SELECT IFNULL((SUM(`debit`) - SUM(`credit`)), 0) AS `balance`
        FROM `tabGL Entry`
        WHERE `account` = "{account}";""".format(account=filters.account), as_dict=True)[0]['balance']
    
    data = [{
        'date': date.today(),
        'balance': balance
    }]
    
    for t in transactions:
        row = t
        balance += t['amount']
        t['balance'] = balance
        data.append(t)
        
    return data
