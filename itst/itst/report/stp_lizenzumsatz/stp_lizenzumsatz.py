# Copyright (c) 2022, ITST, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import calendar
import datetime

def execute(filters=None):
    columns, data = [], []
            
    columns = get_columns()
    
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'batch', 'label': _('Batch'), 'fieldtype': 'Link', 'options': 'Batch', 'width': 100},
        {'fieldname': 'item', 'label': _('Item'), 'fieldtype': 'Link', 'options': 'Item', 'width': 100},
        {'fieldname': 'in_date', 'label': _('In Date'), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'in_qty', 'label': _('In Qty'), 'fieldtype': 'Float', 'width': 75, 'precision': 1},
        {'fieldname': 'out_date', 'label': _('Out Date'), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'out_qty', 'label': _('Out Qty'), 'fieldtype': 'Float', 'width': 75, 'precision': 1},
        {'fieldname': 'customer', 'label': _('Customer'), 'fieldtype': 'Link', 'options': 'Customer', 'width': 100},
        {'fieldname': 'customer_name', 'label': _('Customer name'), 'fieldtype': 'Data', 'width': 150},
        {'fieldname': 'net_volume', 'label': _('Volume'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'details', 'label': _('Details'), 'fieldtype': 'Data', 'width': 200},
    ]
    
def get_data(filters):
    if filters.item_group:
        item_group = filters.item_group
    else:
        item_group = "%"
    if filters.from_date:
        from_date = filters.from_date
    else:
        from_date = "2000-01-01"
    if filters.to_date:
        to_date = filters.to_date
    else:
        to_date = "2099-12-31"
    sql_query = """
        SELECT
            `out`.`batch`,
            `out`.`item`,
            `out`.`item_group`,
            `out`.`out_dn`,
            `out`.`out_date`,
            `out`.`customer`,
            `out`.`customer_name`,
            `out`.`net_volume`,
            `out`.`out_qty`,
            `out`.`details`,
            `in`.`batch`,
            `in`.`in_dn`,
            `in`.`in_date`,
            `in`.`in_qty`
        FROM (
            SELECT 
                `tabBatch`.`name` AS `batch`,
                `tabPurchase Receipt Item`.`parent` AS `in_dn`,
                MAX(`tabPurchase Receipt`.`posting_date`) AS `in_date`,
                SUM(`tabPurchase Receipt Item`.`qty`) AS `in_qty`
            FROM `tabBatch`
            LEFT JOIN `tabPurchase Receipt Item` ON (`tabPurchase Receipt Item`.`batch_no` = `tabBatch`.`name` )
            LEFT JOIN `tabPurchase Receipt` ON `tabPurchase Receipt`.`name` = `tabPurchase Receipt Item`.`parent`
            WHERE 
                `tabBatch`.`item_group` LIKE "{item_group}"
                AND `tabPurchase Receipt`.`posting_date` >= "{from_date}" 
                AND `tabPurchase Receipt`.`posting_date` <= "{to_date}"
            GROUP BY `tabBatch`.`name`
        ) AS `in`
        LEFT JOIN (
            SELECT 
                `tabBatch`.`name` AS `batch`,
                `tabBatch`.`item` AS `item`,
                `tabBatch`.`item_group` AS `item_group`,
                `tabDelivery Note Item`.`parent` AS `out_dn`,
                MAX(`tabDelivery Note`.`posting_date`) AS `out_date`,
                IFNULL(`tabBatch`.`end_customer`, `tabBatch`.`customer`) AS `customer`,
                IFNULL(`tabBatch`.`end_customer_name`,`tabBatch`.`customer_name`) AS `customer_name`,
                SUM(`tabDelivery Note Item`.`base_net_amount`) AS `net_volume`,
                SUM(`tabDelivery Note Item`.`qty`) AS `out_qty`,
                `tabBatch`.`description` AS `details`
            FROM `tabBatch`
            LEFT JOIN `tabDelivery Note Item` ON (`tabDelivery Note Item`.`batch_no` = `tabBatch`.`name` )
            LEFT JOIN `tabDelivery Note` ON `tabDelivery Note`.`name` = `tabDelivery Note Item`.`parent`
            WHERE 
                `tabBatch`.`item_group` LIKE "{item_group}"
                AND `tabDelivery Note`.`posting_date` >= "{from_date}" 
                AND `tabDelivery Note`.`posting_date` <= "{to_date}"
            GROUP BY `tabBatch`.`name`
        ) AS `out`
        ON `in`.`batch` = `out`.`batch`
        
        
    """.format(item_group=item_group, from_date=from_date, to_date=to_date)
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
