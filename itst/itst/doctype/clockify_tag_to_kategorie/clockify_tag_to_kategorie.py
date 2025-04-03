# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
import frappe

class ClockifyTagtoKategorie(Document):	
	def autoname(self):
		kategorie = self.kategorie or "None"
		self.name = kategorie