# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def get_invoiceable_timesheets(from_date, to_date, project):
    sql_query = """
        SELECT 
            `tabTimesheet Detail`.`name` AS `ts_detail`, 
            `tabTimesheet Detail`.`parent` AS `timesheet`, 
            `tabTimesheet Detail`.`billing_hours` AS `billing_hours`, 
            `tabTimesheet Detail`.`hours` AS `hours`, 
            `tabTimesheet Detail`.`remarks` AS `remarks`, 
            `tabTimesheet Detail`.`billing_rate` AS `billing_rate`,
            `tabTimesheet Detail`.`category` AS `category`,
            `tabTimesheet Detail`.`activity_type` AS `activity_type`,
            `tabTimesheet Detail`.`from_time` AS `from_time`
        FROM `tabTimesheet Detail`
        LEFT JOIN `tabTimesheet` ON `tabTimesheet`.`name` = `tabTimesheet Detail`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON (
            `tabTimesheet Detail`.`name` = `tabSales Invoice Item`.`ts_detail`
            AND `tabSales Invoice Item`.`docstatus` < 2
        )
        WHERE 
            `tabTimesheet Detail`.`from_time` >= "{from_date}"
            AND `tabTimesheet Detail`.`from_time` <= "{to_date}"
            AND `tabTimesheet Detail`.`project` = "{project}"
            AND `tabTimesheet`.`docstatus` = 1
            AND `tabTimesheet Detail`.`billable` = 1
            AND `tabSales Invoice Item`.`name` IS NULL;
    """.format(from_date=from_date, to_date=to_date, project=project)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
  
@frappe.whitelist()
def test():
    return "all good"

@frappe.whitelist()
def create_accrual_jv(amount, debit_account, credit_account, date, remarks):
    jv = frappe.get_doc({
        'doctype': 'Journal Entry',
        'posting_date': date,
        'accounts': [{
            'account': debit_account,
            'debit_in_account_currency': amount
        },
        {
            'account': credit_account,
            'credit_in_account_currency': amount
        }],
        'user_remark': remarks
    })
    jv.insert(ignore_permissions=True)
    jv.submit()
    
    return jv.name
