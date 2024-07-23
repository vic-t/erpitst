# Copyright (c) 2022-2024, ITST, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import calendar
import datetime
from frappe.utils import cint

def execute(filters=None):
    columns, data = [], []
            
    columns = get_columns()
    
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'project', 'label': _('Project'), 'fieldtype': 'Link', 'options': 'Project', 'width': 150},
        {'fieldname': 'customer', 'label': _('Customer'), 'fieldtype': 'Link', 'options': 'Customer', 'width': 75},
        {'fieldname': 'customer_name', 'label': _('Customer name'), 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'employee', 'label': _('Employee'), 'fieldtype': 'Link', 'options': 'Employee', 'width': 100},
        {'fieldname': 'employee_name', 'label': _('Full name'), 'fieldtype': 'Data', 'width': 100},
        {'fieldname': 'activity', 'label': _('Activity'), 'fieldtype': 'Data', 'width': 100},
        {'fieldname': 'remarks', 'label': _('Beschreibung'), 'fieldtype': 'Data', 'width': 200},
        {'fieldname': 'category', 'label': _('DL-Artikel'), 'fieldtype': 'Link', 'options': 'Item', 'width': 100},
        {'fieldname': 'billing_hours', 'label': _('Billing Hours'), 'fieldtype': 'Float', 'width': 100},
        {'fieldname': 'billing_amount', 'label': _('Billing Amount'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'hours', 'label': _('Hours'), 'fieldtype': 'Float', 'width': 100},
        {'fieldname': 'costing_amount', 'label': _('Costing Amount'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'oldest', 'label': _('Oldest'), 'fieldtype': 'Date', 'width': 150},
        {'fieldname': 'newest', 'label': _('Newest'), 'fieldtype': 'Date', 'width': 150},
        {'fieldname': 'timesheet', 'label': _('Timesheet'), 'fieldtype': 'Link', 'options': 'Timesheet', 'width': 100},
        {'fieldname': 'task', 'label': _('Task'), 'fieldtype': 'Link', 'options': 'Task', 'width': 120},
        {'fieldname': 'status', 'label': _('Status'), 'fieldtype': 'Data', 'width': 80},
        {'fieldname': 'sales_invoice', 'label': _('Sales Invoice'), 'fieldtype': 'Link', 'options': 'Sales Invoice', 'width': 100},
    ]
    
def get_data(filters):
    if filters.project:
        project = filters.project
    else:
        project = "%"
    if filters.customer:
        customer_condition = """(`tabProject`.`customer` = "{0}") """.format(filters.customer)
    else:
        customer_condition = """(`tabProject`.`customer` IS NULL OR `tabProject`.`customer` LIKE "%") """
    if filters.from_date:
        from_date = filters.from_date
    else:
        from_date = "2000-01-01"
    if filters.to_date:
        to_date = filters.to_date
    else:
        to_date = "2099-12-31"
    if filters.employee:
        customer_condition += """ AND `tabTimesheet`.`employee` = "{employee}" """.format(employee=filters.employee)
    if filters.task:
        customer_condition += """ AND `tabTimesheet Detail`.`task` = "{task}" """.format(task=filters.task)
        
    # if show all: no project status filters, otherwise only open
    if cint(filters.show_all) == 0:
        customer_condition += """ AND  `tabProject`.`status` = "Open" """
    
    # if show_invoiced positions: = 1 no filter, otherwise only uninvoiced
    if cint(filters.show_invoiced) == 0:
        customer_condition += """ AND `tabSales Invoice Item`.`name` IS NULL """
    
    sql_query = """
        SELECT 
            `tabTimesheet Detail`.`project` AS `project`, 
            `tabProject`.`customer` AS `customer`, 
            SUM(`tabTimesheet Detail`.`billing_hours`) AS `billing_hours`,
            SUM(`tabTimesheet Detail`.`billing_hours`) AS `hours`,
            SUM(`tabTimesheet Detail`.`billing_amount`) AS `billing_amount`, 
            SUM(`tabTimesheet Detail`.`costing_amount`) AS `costing_amount`, 
            MIN(`tabTimesheet Detail`.`from_time`) AS `oldest`,
            MAX(`tabTimesheet Detail`.`to_time`) AS `newest`,
            `tabCustomer`.`customer_name` AS `customer_name`,
            `tabProject`.`status` AS `status`,
            0 AS `indent`
        FROM `tabTimesheet Detail`
        LEFT JOIN `tabTimesheet` ON `tabTimesheet`.`name` = `tabTimesheet Detail`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON (
            `tabTimesheet Detail`.`name` = `tabSales Invoice Item`.`ts_detail`
            AND `tabSales Invoice Item`.`docstatus` < 2
        )
        LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
        LEFT JOIN `tabProject` ON `tabProject`.name = `tabTimesheet Detail`.`project`
        LEFT JOIN `tabCustomer` ON `tabCustomer`.`name` = `tabProject`.`customer`
        WHERE 
           `tabTimesheet`.`docstatus` = 1
           AND `tabTimesheet Detail`.`project` IS NOT NULL
           AND `tabTimesheet Detail`.`project` LIKE "{project}"
           AND ((`tabTimesheet Detail`.`from_time` >= "{from_date}" AND `tabTimesheet Detail`.`from_time` <= "{to_date}")
            OR (`tabTimesheet Detail`.`to_time` >= "{from_date}" AND `tabTimesheet Detail`.`to_time` <= "{to_date}"))
           AND `tabSales Invoice`.`posting_date` <= "{to_date}"
           AND `tabSales Invoice`.`posting_date` >= "{from_date}"
           AND {customer_condition}
        GROUP BY 
            `tabTimesheet Detail`.`project`;
    """.format(project=project, from_date=from_date, to_date=to_date, customer_condition=customer_condition)
    projects = frappe.db.sql(sql_query, as_dict=True)
    
    data = []
    # create drill-down
    for p in projects:
        # append project row
        data.append(p)
        # extend drill-down here
        sql_query = """
            SELECT 
                `tabTimesheet Detail`.`project` AS `project`, 
                `tabTimesheet Detail`.`task` AS `task`, 
                `tabProject`.`customer` AS `customer`, 
                SUM(`tabTimesheet Detail`.`billing_hours`) AS `billing_hours`,
                SUM(`tabTimesheet Detail`.`billing_hours`) AS `hours`,
                SUM(`tabTimesheet Detail`.`billing_amount`) AS `billing_amount`, 
                SUM(`tabTimesheet Detail`.`costing_amount`) AS `costing_amount`, 
                MIN(`tabTimesheet Detail`.`from_time`) AS `oldest`,
                MAX(`tabTimesheet Detail`.`to_time`) AS `newest`,
                `tabCustomer`.`customer_name` AS `customer_name`,
                `tabTimesheet`.`employee` AS `employee`,
                `tabTimesheet`.`name` AS `timesheet`,
                `tabTimesheet`.`employee_name` AS `employee_name`,  
                `tabTimesheet Detail`.`activity_type` AS `activity`, 
                `tabTimesheet Detail`.`remarks` AS `remarks`, 
                `tabTimesheet Detail`.`category` AS `category`, 
                `tabProject`.`status` AS `status`,
                `tabSales Invoice Item`.`parent` AS `sales_invoice`,
                1 AS `indent`
            FROM `tabTimesheet Detail`
            LEFT JOIN `tabTimesheet` ON `tabTimesheet`.`name` = `tabTimesheet Detail`.`parent`
            LEFT JOIN `tabSales Invoice Item` ON (
                `tabTimesheet Detail`.`name` = `tabSales Invoice Item`.`ts_detail`
                AND `tabSales Invoice Item`.`docstatus` < 2
            )
            LEFT JOIN `tabProject` ON `tabProject`.name = `tabTimesheet Detail`.`project`
            LEFT JOIN `tabCustomer` ON `tabCustomer`.`name` = `tabProject`.`customer`
            WHERE 
               `tabTimesheet`.`docstatus` = 1
               AND `tabTimesheet Detail`.`project` IS NOT NULL
               AND `tabTimesheet Detail`.`project` = "{project}"
               AND ((`tabTimesheet Detail`.`from_time` >= "{from_date}" AND `tabTimesheet Detail`.`from_time` <= "{to_date}")
                OR (`tabTimesheet Detail`.`to_time` >= "{from_date}" AND `tabTimesheet Detail`.`to_time` <= "{to_date}"))
               AND {customer_condition}
            GROUP BY `tabTimesheet Detail`.`name`
            ORDER BY `tabTimesheet Detail`.`from_time` ASC;
        """.format(project=p['project'], from_date=from_date, to_date=to_date, customer_condition=customer_condition)
        timesheets = frappe.db.sql(sql_query, as_dict=True)
        for t in timesheets:
            data.append(t)
    return data
