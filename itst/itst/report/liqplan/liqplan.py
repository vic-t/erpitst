# Copyright (c) 2022, libracore, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import date
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.utils import cint

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
    
def get_data(filters, only_heads=False):
    dates = get_dates()
    data = []
    # opportunities
    _data = {
        'description': "Chancen"
    }
    if not only_heads:
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
    if not only_heads:
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
    if not only_heads:
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
    if not only_heads:
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
    
    # sales invoices
    _data = {
        'description': "Rechnungen"
    }
    if not only_heads:
        for i in range(1,13):
            if i < 4:
                _data["m{0}".format(i)] = frappe.db.sql("""
                    SELECT IFNULL(SUM(`outstanding_amount`), 0) AS `sum`
                    FROM `tabSales Invoice`
                    WHERE `due_date` > "{from_date}" 
                      AND `due_date` <= "{end_date}"
                      AND `docstatus` = 1;
                    """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
            else:
                _data["m{0}".format(i)] = 0
    data.append(_data)
    
    # purchase invoices
    _data = {
        'description': "Lieferantenrechnungen"
    }
    if not only_heads:
        for i in range(1,13):
            if i < 4:
                _data["m{0}".format(i)] = frappe.db.sql("""
                    SELECT (-1) * IFNULL(SUM(`outstanding_amount`), 0) AS `sum`
                    FROM `tabPurchase Invoice`
                    WHERE `due_date` > "{from_date}" 
                      AND `due_date` <= "{end_date}"
                      AND `docstatus` < 2;
                    """.format(from_date=dates[i-1], end_date=dates[i]), as_dict=True)[0]['sum']
            else:
                _data["m{0}".format(i)] = 0
    data.append(_data)
    
    # add values from budget
    budget_accounts = get_budget_acounts()
    for account in budget_accounts:
        _data = {
            'description': account['account']
        }
        if not only_heads:
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

def get_dates():
    return [
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
    
def get_query(method, from_date, to_date):
    if method == "Chancen":
        return """
            SELECT 
                `name`,
                (`opportunity_amount` * `probability` / 100) AS `amount`
            FROM `tabOpportunity`
            WHERE `transaction_date` > "{from_date}" 
              AND `transaction_date` <= "{end_date}"
              AND `status` = "Open";
            """.format(from_date=from_date, end_date=to_date)
    elif method == "Angebote":
        return """
            SELECT 
                `name`,
                (`base_net_total` * 0.65) AS `amount`
            FROM `tabQuotation`
                    WHERE `valid_till` > "{from_date}" 
                      AND `valid_till` <= "{end_date}"
                      AND `docstatus` = 1
                      AND `status` = "Open";
            """.format(from_date=from_date, end_date=to_date)
    elif method == "Aufträge":
        return """
            SELECT 
                `name`,
                (`base_net_total` * 0.85) AS `amount`
            FROM `tabSales Order`
                    WHERE `delivery_date` > "{from_date}" 
                      AND `delivery_date` <= "{end_date}"
                      AND `docstatus` = 1;
            """.format(from_date=from_date, end_date=to_date)
    elif method == "Support":
        return """
            SELECT 
                `tabSales Invoice`.`name`,
                (`tabSales Invoice Item`.`base_net_amount` * 0.9) AS `amount`
            FROM `tabSales Invoice Item`
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
            WHERE `tabSales Invoice`.`posting_date` > "{from_date}" 
              AND `tabSales Invoice`.`posting_date` <= "{end_date}"
              AND `tabSales Invoice`.`docstatus` = 1
              AND `tabSales Invoice Item`.`item_code` = "IT-Support";
            """.format(from_date=date.today() + relativedelta(months=-3), end_date=date.today())
    elif method == "Rechnungen":
        return """
            SELECT 
                `tabSales Invoice`.`name`,
                `tabSales Invoice`.`outstanding_amount` AS `amount`
            FROM `tabSales Invoice`
            WHERE `tabSales Invoice`.`due_date` > "{from_date}" 
              AND `tabSales Invoice`.`due_date` <= "{end_date}"
              AND `tabSales Invoice`.`docstatus` = 1;
            """.format(from_date=from_date, end_date=to_date)
    elif method == "Lieferantenrechnungen":
        return """
            SELECT 
                `tabPurchase Invoice`.`name`,
                (-1) * `tabPurchase Invoice`.`outstanding_amount` AS `amount`
            FROM `tabPurchase Invoice`
            WHERE `tabPurchase Invoice`.`due_date` > "{from_date}" 
              AND `tabPurchase Invoice`.`due_date` <= "{end_date}"
              AND `tabPurchase Invoice`.`docstatus` < 2;
            """.format(from_date=from_date, end_date=to_date)
    elif frappe.db.exists("Account", method):
        return """
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
            """.format(date=to_date, month=get_month_from_date(to_date), account=method)
    else:
        return ""
    
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
    month = get_month_from_date(date)
        
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

def get_month_from_date(date):
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
    return month_mapping[month_int]

@frappe.whitelist()
def show_details(row, column):
    if cint(column) > 1:
        dates = get_dates()
        methods = get_data(None, only_heads=True)
        sql_query = get_query(methods[cint(row)]['description'], dates[cint(column)-2], dates[cint(column)-1])
        if sql_query:
            output = frappe.db.sql(sql_query, as_dict=True)
            html = "<table class=\"table\"><thead><tr><th>Name</th><th>Betrag</th></tr></thead><tbody>";
            for o in output:
                html += "<tr><td>{0}</td><td>{1}</td></tr>".format(o['name'], o['amount'])
            html += "</tbody></table>"
            frappe.msgprint("{0}".format(html), "Details")
