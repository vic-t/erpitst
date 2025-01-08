# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

from itst.itst.integrations.clockify_integration import (
    parse_duration
)


class TestClockifyIntegration(unittest.TestCase):
    def should_ReturnCorrectDuration_When_ParsingDurationToDuration(self):
        duration_str = parse_duration("PT1H30M")
        self.assertEqual(duration_str, "1:30")

    def should_ReturnCorrectHour_When_ParsingDurationToHour(self):
        hours = parse_duration("PT2H15M")
        self.assertEqual(hours, 2.25)

    def should_RetrunError_When_InvalidStringIsPassed(self):
        with self.assertRaises(frappe.ValidationError):
            parse_duration("XYZ")

