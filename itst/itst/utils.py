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

@frappe.whitelist()
def create_combined_pdf(dt, dn, print_format):
    # first, fill cover page
    doc = frappe.get_doc(dt, dn)
    data = {
        'customer': doc.customer_name,
        'date': doc.get_formatted('posting_Date'),
        'title': doc.title
    }
    # generate pdf
    generated_pdf = pypdftk.fill_form("{0}/sites/{1}/coverpage.pdf".format(get_bench_path(), get_files_path()[1:]), data)
    with open(generated_pdf, mode='rb') as file:
        cover_pdf_data = file.read()
    # create normal print format
    html = frappe.get_print(dt, dn, print_format)
    content_pdf = frappe.utils.pdf.get_pdf(html)
    # merge the two
    merger = PdfFileMerger()
    merger.append(cover_pdf_data)
    merger.append(content_pdf)
    tmp_name = "/tmp/{0}.pdf".format(uuid.uuid4().hex)
    merger.write(tmp_name)
    merger.close()
    # load and attach
    with open(tmp_name, mode='rb') as file:
        combined_pdf_data = file.read()
    file_name = "{}.pdf".format(doc.name.replace(" ", "-").replace("/", "-"))
    save_file(file_name, combined_pdf_data, dt,
              dn, folder="Attachments", is_private=1)   
    return
