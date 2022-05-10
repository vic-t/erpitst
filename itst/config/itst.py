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
                   },
                   {
                       "type": "report",
                       "name": "STP Lizenzumsatz",
                       "label": _("STP Lizenzumsatz"),
                       "doctype": "Serial No",
                       "is_query_report": True
                   },
                   {
                       "type": "report",
                       "name": "Offene TS-Positionen",
                       "label": _("Offene TS-Positionen"),
                       "doctype": "Timesheet",
                       "is_query_report": True
                   }
            ]
        },
        {
            "label": _("Einstellungen"),
            "icon": "octicon octicon-repo",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Signature",
                       "label": _("Signature"),
                       "description": _("Signature")
                   },
                   {
                       "type": "doctype",
                       "name": "Email Footer Temaplte",
                       "label": _("Email Footer Temaplte"),
                       "description": _("Email Footer Temaplte")
                   },
                   {
                       "type": "doctype",
                       "name": "Batch",
                       "label": _("Batch"),
                       "description": _("Batch")
                   }
            ]
        }
    ]
