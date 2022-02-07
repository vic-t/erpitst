# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for activity item (category)
def activity_item(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabItem`.`name`, `tabItem`.`item_group`
           FROM `tabItem`
           WHERE `tabItem`.`item_group` LIKE "%{c}%" AND `tabItem`.`name` LIKE "%{s}%";
        """.format(c=filters['keyword'], s=txt))
  
