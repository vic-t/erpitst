# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class ClockifyTagtoArtikel(Document):
	def autoname(self):
		artikel = self.artikel or "None"
		self.name = artikel
