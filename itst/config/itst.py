from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Finanzbuchhaltung"),
            "icon": "octicon octicon-repo",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Payment Reminder",
                       "label": _("Payment Reminder"),
                       "description": _("Payment Reminder")
                   },
                   {
                       "type": "doctype",
                       "name": "Payment Proposal",
                       "label": _("Payment Proposal"),
                       "description": _("Payment Proposal")
                   },
                   {
                       "type": "page",
                       "name": "bank_wizard",
                       "label": _("Bank Wizard"),
                       "description": _("Bank Wizard")
                   }
            ]
        },
        {
            "label": _("Vertrieb"),
            "icon": "octicon octicon-repo",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Customer",
                       "label": _("Customer"),
                       "description": _("Customer")
                   },
                   {
                       "type": "doctype",
                       "name": "Quotation",
                       "label": _("Quotation"),
                       "description": _("Quotation")
                   },
                   {
                       "type": "doctype",
                       "name": "Sales Order",
                       "label": _("Sales Order"),
                       "description": _("Sales Order")
                   },
                   {
                       "type": "doctype",
                       "name": "Delivery Note",
                       "label": _("Delivery Note"),
                       "description": _("Delivery Note")
                   },
                   {
                       "type": "doctype",
                       "name": "Sales Invoice",
                       "label": _("Sales Invoice"),
                       "description": _("Sales Invoice")
                   },
                   {
                       "type": "doctype",
                       "name": "Abo",
                       "label": _("Abo"),
                       "description": _("Abo")
                   }
            ]
        },
        {
            "label": _("Berichte"),
            "icon": "octicon octicon-repo",
            "items": [
                   {
                       "type": "report",
                       "name": "Kommissionsberechnung",
                       "label": _("Kommissionsberechnung"),
                       "doctype": "Sales Invoice",
                       "is_query_report": True
                   }
            ]
        }
    ]
