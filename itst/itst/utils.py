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
            `tabTimesheet Detail`.`remarks` AS `remarks`, 
            `tabTimesheet Detail`.`billing_rate` AS `billing_rate`,
            `tabTimesheet Detail`.`category` AS `category`
        FROM `tabTimesheet Detail`
        LEFT JOIN `tabTimesheet` ON `tabTimesheet`.`name` = `tabTimesheet Detail`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON (
            `tabTimesheet Detail`.`name` = `tabSales Invoice Item`.`ts_detail`
            AND `tabSales Invoice Item`.`docstatus` < 2
        )
        WHERE 
            `tabTimesheet Detail`.`from_time` >= "{from_date}"
            AND `tabTimesheet Detail`.`from_time` >= "{to_date}"
            AND `tabTimesheet Detail`.`project` = "{project}"
            AND `tabTimesheet`.`docstatus` = 1;
    """.format(from_date=from_date, to_date=to_date, project=project)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
  
@frappe.whitelist()
def test():
    return "all good"
