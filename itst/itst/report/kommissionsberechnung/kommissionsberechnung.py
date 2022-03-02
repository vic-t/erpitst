# Copyright (c) 2022, ITST, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import calendar
import datetime

def execute(filters=None):
    columns, data = [], []
    
    # get configuration
    sales_partner = frappe.get_doc("Sales Partner", filters.sales_partner)
    
    # prepare recursive groups
    item_groups = {}
    for c in sales_partner.commissions:
        if c.item_group not in item_groups:
            item_groups[c.item_group] = get_child_groups(c.item_group)
    
    # prepare data range
    first_last_day = calendar.monthrange(filters.year, filters.month)
    from_date = datetime.datetime(filters.year, filters.month, first_last_day[0]).date()
    to_date = datetime.datetime(filters.year, filters.month, first_last_day[1]).date()
    ytd_from = datetime.datetime(filters.year, 1, 1).date()
    if filters.month < 4:
        start_q = datetime.datetime(filters.year, 1, 1).date()
        end_q = datetime.datetime(filters.year, 3, 31).date()
    elif filters.month < 7:
        start_q = datetime.datetime(filters.year, 4, 1).date()
        end_q = datetime.datetime(filters.year, 6, 30).date()
    elif filters.month < 10:
        start_q = datetime.datetime(filters.year, 7, 1).date()
        end_q = datetime.datetime(filters.year, 9, 30).date()
    else:
        start_q = datetime.datetime(filters.year, 10, 1).date()
        end_q = datetime.datetime(filters.year, 12, 31).date()
        
    columns = [
        {'fieldname': 'item_group', 'label': _('Item Group'), 'fieldtype': 'Link', 'options': 'Item Group', 'width': 100}, 
        {'fieldname': 'volume', 'label': _('Volume'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'volume_ytd', 'label': _('Volume YTD'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'commission_rate', 'label': _('Commission %'), 'fieldtype': 'Percent', 'width': 100},
        {'fieldname': 'commission', 'label': _('Commission'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'volume_q', 'label': _('Volume Quarter'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'target', 'label': _('Target'), 'fieldtype': 'Currency', 'width': 100},
        {'fieldname': 'achievement', 'label': _('Achievement'), 'fieldtype': 'Percent', 'width': 100},
        {'fieldname': 'bonus', 'label': _('Bonus'), 'fieldtype': 'Currency', 'width': 100},
    ]
    
    data = []
    totals = {'volume': 0, 'volume_ytd': 0, 'volume_q': 0, 'commission': 0, 'bonus': 0}
    for k, v in item_groups.items():
        row = {
            'item_group': k,
            'volume': get_volume(filters.sales_partner, from_date, to_date, v),
            'volume_ytd': get_volume(filters.sales_partner, ytd_from, to_date, v),
            'volume_q': get_volume(filters.sales_partner, start_q, end_q, v)
        }
        # find commission rate based on ytd
        for c in sales_partner.commissions:
            if c.item_group == k and row['volume_ytd'] >= c.from_amount and row['volume_ytd'] <= c.to_amount:
                row['commission_rate'] = c.provision
                break
        if 'commission_rate' not in row:
            row['commission_rate'] = 0
        # set commission amount
        row['commission'] = row['volume'] * (row['commission_rate'] / 100)
        
        # bonus calculation
        target = 1
        for b in sales_partner.bonus:
            if b.item_group == k:
                target = b.target
                break
        row['target'] = target or 1
        row['achievement'] = 100 * row['volume_q'] / (target or 1)
        if filters.month == 3 or filters.month == 6 or filters.month == 9 or filters.month == 12:
            bonus = 0
            for b in sales_partner.bonus:
                if b.item_group == k and row['achievement'] >= b.achievement:
                    bonus += b.bonus_amount
            row['bonus'] = bonus
        else:
            row['bonus'] = 0
        data.append(row)

        # add to totals
        totals['volume'] += row['volume']
        totals['volume_ytd'] += row['volume_ytd']
        totals['volume_q'] += row['volume_q']
        totals['commission'] += row['commission']
        totals['bonus'] += row['bonus']

    data.append(totals)
    return columns, data

def get_volume(sales_partner, from_date, to_date, item_groups):
    sql_query = """SELECT
            IFNULL(SUM(`tabSales Invoice Item`.`base_net_amount`), 0) AS `volume`
        FROM `tabSales Invoice Item`
        LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
        WHERE
            `tabSales Invoice`.`docstatus` = 1 
            AND `tabSales Invoice`.`posting_date` >= "{from_date}"
            AND `tabSales Invoice`.`posting_date` <= "{to_date}"
            AND `tabSales Invoice`.`sales_partner` = "{sales_partner}"
            AND `tabSales Invoice Item`.`item_group` IN ({item_groups})
        ;""".format(
            from_date=from_date, to_date=to_date, sales_partner=sales_partner, 
            item_groups=', '.join('"{0}"'.format(w) for w in item_groups))
    row = frappe.db.sql(sql_query, as_dict = True)
    return row[0]['volume']
    
def get_child_groups(item_group):
    children = frappe.get_all("Item Group", filters={'parent_item_group': item_group}, fields=['name'])
    children_list = [item_group]
    for c in children:
        subs = get_child_groups(c['name'])
        for s in subs:
            children_list.append(s)
    return children_list
