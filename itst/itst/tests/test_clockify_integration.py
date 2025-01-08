# -*- coding: utf-8 -*-
# Copyright (c) 2025, ITST and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

from itst.itst.integrations.clockify_integration import (
    parse_duration,
    parse_hhmm_to_minutes,
    minutes_to_hhmm,
    round_minutes_to_5
)


class TestClockifyIntegration(unittest.TestCase):
    
    #Tests for parse_duration
    def should_ReturnCorrectDuration_When_ParsingDurationToDuration(self):
        duration_str = parse_duration("PT1H30M")
        self.assertEqual(duration_str, "1:30")

    def should_ReturnCorrectHour_When_ParsingDurationToHour(self):
        hours = parse_duration("PT2H15M")
        self.assertEqual(hours, 2.25)

    def should_RetrunError_When_InvalidStringIsPassed(self):
        with self.assertRaises(frappe.ValidationError):
            parse_duration("XYZ")

    #Test for parse_hhmm_to_minutes
    def should_ReturnNumerIn5MinuteInterval_When_ANumberInhhmmFormatIsGiven(self):
        total_minutes = parse_hhmm_to_minutes("2:05")
        self.assertEqual(total_minutes, 125)

    #Test for minutes_to_hhmm
    def should_ReturnNumerinhhmmFormat_When_ANumberIn5MinuteIntervalIsGiven(self):
        hhmm = minutes_to_hhmm(125)
        self.assertEqual(hhmm, "2:05")
    
    #Test for round_minutes_to_5
    def should_RoundToTheNext5MinuteIntervalNumber_When_ANumberIsGiven(self):
        self.assertEqual(round_minutes_to_5(123), 125)
        self.assertEqual(round_minutes_to_5(88), 90)
