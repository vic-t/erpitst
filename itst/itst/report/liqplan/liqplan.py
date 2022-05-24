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
    for i in range(1,13):
        if i < 4:
            _data["m{0}".format(i)] = frappe.db.sql("""
                SELECT IFNULL(SUM(`opportunity_amount` * `probability` / 100), 0) AS `sum`
                FROM `tabOpportunity`
                WHERE `transaction_date` > "{from_date}" 
                  AND `transaction_date` <= "{end_date}"
                  AND `status` = "Open";
                """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
        else:
            _data["m{0}".format(i)] = 0
    data.append(_data)
    
    # quotations
    _data = {
        'description': "Angebote"
    }
    for i in range(1,13):
        if i < 4:
            _data["m{0}".format(i)] = frappe.db.sql("""
                SELECT IFNULL(SUM(`base_net_total` * 0.65), 0) AS `sum`
                FROM `tabQuotation`
                WHERE `valid_till` > "{from_date}" 
                  AND `valid_till` <= "{end_date}"
                  AND `docstatus` = 1
                  AND `status` = "Open";
                """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
        else:
            _data["m{0}".format(i)] = 0
    data.append(_data)
    
    # sales orders
    _data = {
        'description': "Aufträge"
    }
    for i in range(1,13):
        if i < 4:
            _data["m{0}".format(i)] = frappe.db.sql("""
                SELECT IFNULL(SUM(`base_net_total` * 0.85), 0) AS `sum`
                FROM `tabSales Order`
                WHERE `delivery_date` > "{from_date}" 
                  AND `delivery_date` <= "{end_date}"
                  AND `docstatus` = 1;
                """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
        else:
            _data["m{0}".format(i)] = 0
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
    for i in range(1,13):
        if i < 4:
            _data["m{0}".format(i)] = 0.9 * (last_average / 3)
        else:
            _data["m{0}".format(i)] = 0
    data.append(_data)
    
    # add values from budget
    budget_accounts = get_budget_acounts()
    for account in budget_accounts:
        _data = {
            'description': account['account']
        }
        for i in range(1,13):
            if account['account_type'] == "Expense Account":
                sign = -1       # expense account
            else:
                if i < 4:
                    sign = 0    # first three months: use sales pipeline instead of budget
                else:
                    sign = 1    # use budget for income
            _data["m{0}".format(i)] = sign * get_monthly_budget(dates[i], account['account'])
            
        data.append(_data)
        
    return data

def get_budget_acounts():
    accounts = frappe.db.sql("""
        SELECT 
            `tabBudget Account`.`account`,
            `tabAccount`.`account_type`
        FROM `tabBudget Account` 
        LEFT JOIN `tabAccount` ON `tabAccount`.`name` = `tabBudget Account`.`account`
        WHERE `tabAccount`.`disabled` = 0
          AND `tabAccount`.`account_type` IN ("Expense Account", "Income Account")
        GROUP BY `tabBudget Account`.`account`
        ORDER BY `tabAccount`.`account_type` DESC, `tabBudget Account`.`account` ASC;
    """, as_dict=True)
    return accounts
    
def get_monthly_budget(date, account):
    month_int = str(date)[5:7]
    month_mapping = {
        '01': 'January',
        '02': 'February',
        '03': 'March',
        '04': 'April',
        '05': 'May',
        '06': 'June',
        '07': 'July',
        '08': 'August',
        '09': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December'
    }
    month = month_mapping[month_int]
        
    sql_query = """
        SELECT 
            `tabBudget`.`name`, 
            `tabFiscal Year`.`year_start_date`,
            `tabFiscal Year`.`year_end_date`,
            `tabBudget Account`.`account`,
            `tabBudget Account`.`budget_amount`,
            `tabMonthly Distribution Percentage`.`month`,
            `tabMonthly Distribution Percentage`.`percentage_allocation`,
            IFNULL(`tabBudget Account`.`budget_amount` * `tabMonthly Distribution Percentage`.`percentage_allocation`/100 , 0) AS `amount`
        FROM `tabBudget Account` 
        LEFT JOIN `tabBudget` ON `tabBudget`.`name` = `tabBudget Account`.`parent`
        LEFT JOIN `tabFiscal Year` ON `tabBudget`.`fiscal_year` = `tabFiscal Year`.`name`
        JOIN `tabMonthly Distribution Percentage` ON `tabMonthly Distribution Percentage`.`parent` = `tabBudget`.`monthly_distribution`
        WHERE `tabFiscal Year`.`year_start_date` <= "{date}"
          AND `tabFiscal Year`.`year_end_date` >= "{date}"
          AND `tabMonthly Distribution Percentage`.`month` = "{month}"
          AND `tabBudget Account`.`account` = "{account}";
    """.format(date=date, month=month, account=account)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    if len(data) > 0:
        return data[0]['amount']
    else:
        return 0
    
