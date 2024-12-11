# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "itst"
app_title = "ITST"
app_publisher = "ITST"
app_description = "ITST"
app_icon = "octicon octicon-file-directory"
app_color = "blue"
app_email = "vt@itst.ch"
app_license = "GPL"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/itst/css/itst.css"
app_include_js = [
    "/assets/itst/js/itst_common.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/itst/css/itst.css"
# web_include_js = "/assets/itst/js/itst.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Customer" : "public/js/customer.js",
    "Item" : "public/js/item.js",
    "Serial No" : "public/js/serial_no.js",
    "Timesheet" : "public/js/timesheet.js",
    "Project" : "public/js/project.js",
    "Delivery Note" : "public/js/delivery_note.js",
    "Task" : "public/js/task.js",
    "Sales Partner" : "public/js/sales_partner.js",
    "Sales Invoice" : "public/js/sales_invoice.js",
    "Payment Entry" : "public/js/payment_entry.js",
    "Opportunity" : "public/js/opportunity.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "itst.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "itst.install.before_install"
# after_install = "itst.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "itst.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"itst.tasks.all"
# 	],
    "daily": [
        "itst.itst.doctype.abo.abo.create_todays_invoices",
        "itst.itst.utils.update_vat_accruals"
    ]
# 	"hourly": [
# 		"itst.tasks.hourly"
# 	],
# 	"weekly": [
# 		"itst.tasks.weekly"
# 	]
# 	"monthly": [
# 		"itst.tasks.monthly"
# 	]
}

# Testing
# -------

# before_tests = "itst.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "itst.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "itst.task.get_dashboard_data"
# }

