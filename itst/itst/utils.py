# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import pypdftk
from frappe.core.doctype.file.file import create_new_folder
from frappe.utils.file_manager import save_file
from PyPDF2 import PdfFileMerger
import uuid
from frappe.utils.file_manager import save_file
from frappe.utils import get_bench_path, get_files_path
import random
import string
import os
from datetime import datetime, timedelta

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
def create_accrual_jv(amount, debit_account, credit_account, date, remarks, document):
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
        'user_remark': remarks,
        'cheque_no': document,
        'cheque_date': date
    })
    jv.insert(ignore_permissions=True)
    jv.submit()
    
    update_stp_accruals()
    
    return jv.name

@frappe.whitelist()
def cancel_accrual_jv(date, document):
    docs = []
    jvs = frappe.get_all("Journal Entry", 
        filters={'docstatus': 1, 'posting_date': date, 'cheque_no': document}, 
        fields=['name'])
    for jv in jvs:
        doc = frappe.get_doc("Journal Entry", jv['name'])
        doc.cancel()
        docs.append(doc.name) 
    update_stp_accruals()
    return ", ".join(docs)

def update_stp_accruals():
    settings = frappe.get_doc("ITST Settings", "ITST Settings")
    if settings.stp_accrual_invoice and settings.stp_accrual_account:
        amount = (-1) * frappe.db.sql("""
            SELECT IFNULL((SUM(`debit`) - SUM(`credit`)), 0) AS `sum`
            FROM `tabGL Entry`
            WHERE `account` = "{0}"
              AND `posting_date` <= CURDATE();""".format(settings.stp_accrual_account), as_dict=True)[0]['sum']
        if amount >= 0:
            update_purchase_invoice(settings.stp_accrual_invoice, amount)
    else:
        frappe.log_error("Unable to create accrual invoice: purchase invoice missing (see ITST Settings)", "update_stp_accrual")
    return

def update_vat_accruals():
    settings = frappe.get_doc("ITST Settings", "ITST Settings")
    if settings.vat_accrual_invoice and settings.vat_accrual_accounts:
        accounts = settings.vat_accrual_accounts.split(",")
        amount = 0
        for account in accounts:
            amount += (-1) * frappe.db.sql("""
                SELECT IFNULL((SUM(`debit`) - SUM(`credit`)), 0) AS `sum`
                FROM `tabGL Entry`
                WHERE `account` LIKE "{0}%"
                  AND `posting_date` <= CURDATE();""".format(account), as_dict=True)[0]['sum']
        if amount >= 0:
            update_purchase_invoice(settings.vat_accrual_invoice, amount)
    else:
        frappe.log_error("Unable to create accrual invoice: purchase invoice missing (see ITST Settings)", "update_vat_accrual")
    return

def update_purchase_invoice(invoice, amount):
    doc = frappe.get_doc("Purchase Invoice", invoice)
    doc.items[0].rate = round(amount, 2)
    doc.set_posting_time = 1
    doc.posting_date = datetime.now()
    doc.payment_schedule = []
    doc.due_date = doc.posting_date + timedelta(days=30)
    doc.save()
    return
    
@frappe.whitelist()
def create_combined_pdf(dt, dn, print_format):
    # first, fill cover page
    doc = frappe.get_doc(dt, dn)
    data = {
        'RecipientName': doc.customer_name,
        'DocDate': doc.get_formatted('transaction_date'),
        'DocTitle': doc.title
    }
    # generate pdf
    generated_pdf = pypdftk.fill_form("{0}/sites{1}/coverpage.pdf".format(get_bench_path(), get_files_path()[1:]), data)
    # create normal print format
    content_pdf = frappe.get_print(dt, dn, print_format=print_format, as_pdf=True)
    content_file_name = "/tmp/{0}.pdf".format(get_random_string(32))
    with open(content_file_name, mode='wb') as file:
        file.write(content_pdf)
    # merge the two
    merger = PdfFileMerger()
    merger.append(generated_pdf)
    merger.append(content_file_name)
    tmp_name = "/tmp/{0}.pdf".format(uuid.uuid4().hex)
    merger.write(tmp_name)
    merger.close()
    cleanup(content_file_name)
    # load and attach
    with open(tmp_name, mode='rb') as file:
        combined_pdf_data = file.read()
    file_name = "{}.pdf".format(doc.name.replace(" ", "-").replace("/", "-"))
    save_file(file_name, combined_pdf_data, dt,
              dn, is_private=1)   
    return

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
    
def cleanup(fname):
    if os.path.exists(fname):
        os.remove(fname)

"""
This function will apply the customer to each linked batch of a delivery note
"""
@frappe.whitelist()
def set_batch_customer(delivery_note):
    dn = frappe.get_doc("Delivery Note", delivery_note)
    for i in dn.items:
        if i.batch_no:
            batch = frappe.get_doc("Batch", i.batch_no)
            batch.customer = dn.customer
            batch.save(ignore_permissions=True)
    frappe.db.commit()
    return
