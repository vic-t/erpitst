# Copyright (c) 2013, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.stock.utils import update_included_uom_in_report

def execute(filters=None):
    include_uom = filters.get("include_uom")
    columns = get_columns()
    items = get_items(filters)
    sl_entries = get_stock_ledger_entries(filters, items)
    item_details = get_item_details(items, sl_entries, include_uom)
    opening_row = get_opening_balance(filters, columns)

    data = []
    conversion_factors = []
    if opening_row:
        data.append(opening_row)

    for sle in sl_entries:
        # item_detail = item_details[sle.item_code]

        # sle.update(item_detail)
        data.append(sle)

        if include_uom:
            conversion_factors.append(item_detail.conversion_factor)

    update_included_uom_in_report(columns, data, include_uom, conversion_factors)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Datetime", "width": 95},
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 100},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 100},
        {"label": _("Description"), "fieldname": "description", "width": 200},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 100},
        {"label": _("Qty"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 50, "convertible": "qty"},
        {"label": _("Balance Qty"), "fieldname": "qty_after_transaction", "fieldtype": "Float", "width": 100, "convertible": "qty"},
        {"label": _("Incoming Rate"), "fieldname": "incoming_rate", "fieldtype": "Currency", "width": 110,
            "options": "Company:company:default_currency", "convertible": "rate"},
        {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 110,
            "options": "Company:company:default_currency", "convertible": "rate"},
        {"label": _("Balance Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 110,
            "options": "Company:company:default_currency"},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
        {"label": _("Voucher #"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 100},
        {"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 100},
        {"label": _("Serial #"), "fieldname": "serial_no", "width": 100},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 110}
    ]

    return columns

def get_stock_ledger_entries(filters, items):
    item_conditions_sql = ''
    if items:
        item_conditions_sql = 'AND `sle`.`item_code` IN ({})'\
            .format(', '.join([frappe.db.escape(i) for i in items]))

    return frappe.db.sql("""
        SELECT 
            CONCAT(`sle`.`posting_date`, " ", `sle`.`posting_time`) AS `date`,
            `sle`.`item_code`, 
            `sle`.`warehouse`, 
            `sle`.`actual_qty`, 
            `sle`.`qty_after_transaction`, 
            `sle`.`incoming_rate`, 
            `sle`.`valuation_rate`,
            `sle`.`stock_value`, 
            `sle`.`voucher_type`, 
            `sle`.`voucher_no`, 
            `sle`.`batch_no`, 
            `sle`.`serial_no`, 
            `sle`.`company`, 
            `sle`.`project`,
            `tabItem`.`item_group`,
            `tabItem`.`stock_uom`,
            IF(`voucher_type` = "Purchase Receipt", 
                `tabPurchase Receipt Item`.`item_name`,
                `tabDelivery Note Item`.`item_name`) AS `item_name`,
            IF(`voucher_type` = "Purchase Receipt", 
                `tabPurchase Receipt Item`.`description`,
                `tabDelivery Note Item`.`description`) AS `description`
        FROM `tabStock Ledger Entry` AS `sle`
        LEFT JOIN `tabItem` ON `tabItem`.`name` = `sle`.`item_code`
        LEFT JOIN `tabPurchase Receipt Item` ON `sle`.`voucher_detail_no` = `tabPurchase Receipt Item`.`name`
        LEFT JOIN `tabDelivery Note Item` ON `sle`.`voucher_detail_no` = `tabDelivery Note Item`.`name`
        WHERE `sle`.`company` = %(company)s AND
            `posting_date` BETWEEN %(from_date)s AND %(to_date)s
            {sle_conditions}
            {item_conditions_sql}
            ORDER BY `sle`.`posting_date` ASC, `sle`.`posting_time` ASC, `sle`.`creation` ASC"""\
        .format(
            sle_conditions=get_sle_conditions(filters),
            item_conditions_sql = item_conditions_sql
        ), filters, as_dict=1)

def get_items(filters):
    conditions = []
    if filters.get("item_code"):
        conditions.append("item.name=%(item_code)s")
    else:
        if filters.get("brand"):
            conditions.append("item.brand=%(brand)s")
        if filters.get("item_group"):
            conditions.append(get_item_group_condition(filters.get("item_group")))

    items = []
    if conditions:
        items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
            .format(" and ".join(conditions)), filters)
    return items

def get_item_details(items, sl_entries, include_uom):
    item_details = {}
    if not items:
        items = list(set([d.item_code for d in sl_entries]))

    if not items:
        return item_details

    cf_field = cf_join = ""
    if include_uom:
        cf_field = ", ucd.conversion_factor"
        cf_join = "left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom='%s'" \
            % (include_uom)

    res = frappe.db.sql("""
        select
            item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom {cf_field}
        from
            `tabItem` item
            {cf_join}
        where
            item.name in ({item_codes})
    """.format(cf_field=cf_field, cf_join=cf_join, item_codes=','.join(['%s'] *len(items))), items, as_dict=1)

    for item in res:
        item_details.setdefault(item.name, item)

    return item_details

def get_sle_conditions(filters):
    conditions = []
    if filters.get("warehouse"):
        warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
        if warehouse_condition:
            conditions.append(warehouse_condition)
    if filters.get("voucher_no"):
        conditions.append("voucher_no=%(voucher_no)s")
    if filters.get("batch_no"):
        conditions.append("batch_no=%(batch_no)s")
    if filters.get("project"):
        conditions.append("project=%(project)s")

    return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_opening_balance(filters, columns):
    if not (filters.item_code and filters.warehouse and filters.from_date):
        return

    from erpnext.stock.stock_ledger import get_previous_sle
    last_entry = get_previous_sle({
        "item_code": filters.item_code,
        "warehouse_condition": get_warehouse_condition(filters.warehouse),
        "posting_date": filters.from_date,
        "posting_time": "00:00:00"
    })
    row = {}
    row["item_code"] = _("'Opening'")
    for dummy, v in ((9, 'qty_after_transaction'), (11, 'valuation_rate'), (12, 'stock_value')):
            row[v] = last_entry.get(v, 0)

    return row

def get_warehouse_condition(warehouse):
    warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
    if warehouse_details:
        return " exists (select name from `tabWarehouse` wh \
            where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
            warehouse_details.rgt)

    return ''

def get_item_group_condition(item_group):
    item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
    if item_group_details:
        return "item.item_group in (select ig.name from `tabItem Group` ig \
            where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
            item_group_details.rgt)

    return ''
