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
        {'fieldname': 'snr', 'label': _('SNR'), 'fieldtype': 'Link', 'options': 'Serial No', 'width': 100},
        {'fieldname': 'item', 'label': _('Item'), 'fieldtype': 'Link', 'options': 'Item', 'width': 100},
        {'fieldname': 'in_date', 'label': _('In Date'), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'out_date', 'label': _('Out Date'), 'fieldtype': 'Date', 'width': 100},
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
            `tabSerial No`.`name` AS `snr`,
            `tabSerial No`.`item_code` AS `item`,
            `tabSerial No`.`item_group` AS `item_group`,
            `tabSerial No`.`purchase_document_type` AS `in_dt`,
            `tabSerial No`.`purchase_document_no` AS `in_dn`,
            `tabSerial No`.`purchase_date` AS `in_date`,
            `tabSerial No`.`delivery_document_type` AS `out_dt`,
            `tabSerial No`.`delivery_document_no` AS `out_dn`,
            `tabSerial No`.`delivery_date` AS `out_date`,
            IFNULL(`tabSerial No`.`end_customer`, `tabSerial No`.`customer`) AS `customer`,
            IFNULL(`tabSerial No`.`end_customer_name`,`tabSerial No`.`customer_name`) AS `customer_name`,
            `tabDelivery Note Item`.`base_rate` AS `net_volume`,
            `tabSerial No`.`serial_no_details` AS `details`
        FROM `tabSerial No`
        LEFT JOIN `tabDelivery Note Item` ON (`tabDelivery Note Item`.`parent` = `tabSerial No`.`delivery_document_no` 
                                AND `tabDelivery Note Item`.`serial_no` LIKE CONCAT("%", `tabSerial No`.`name`, "%"))
        WHERE 
            `tabSerial No`.`item_group` LIKE "{item_group}"
            AND ((`tabSerial No`.`purchase_date` >= "{from_date}" AND `tabSerial No`.`purchase_date` <= "{to_date}")
            OR (`tabSerial No`.`delivery_date` >= "{from_date}" AND `tabSerial No`.`delivery_date` <= "{to_date}"))
    """.format(item_group=item_group, from_date=from_date, to_date=to_date)
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
