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
    round_minutes_to_5,
    convert_iso_to_erpnext_datetime,
    build_html_link
)


class TestClockifyIntegration(unittest.TestCase):

    def test_basic_assertion(self):
          self.assertTrue(True, "Dies ist nur ein Dummy-Test, der immer True ist.")

    #Tests for parse_duration
    def test_should_ReturnCorrectDurationAndHour_When_ParsingDuration(self):
        hours, duration_str = parse_duration("PT1H30M")
        self.assertEqual(hours, 1.5)
        self.assertEqual(duration_str, "1:30")

    def test_should_RetrunError_When_InvalidStringIsPassed(self):
        with self.assertRaises(frappe.ValidationError):
            parse_duration("XYZ")

    #Test for parse_hhmm_to_minutes
    def test_should_ReturnNumerIn5MinuteInterval_When_ANumberInhhmmFormatIsGiven(self):
        total_minutes = parse_hhmm_to_minutes("2:05")
        self.assertEqual(total_minutes, 125)

    #Test for minutes_to_hhmm
    def test_should_ReturnNumerinhhmmFormat_When_ANumberIn5MinuteIntervalIsGiven(self):
        hhmm = minutes_to_hhmm(125)
        self.assertEqual(hhmm, "2:05")
    
    #Test for round_minutes_to_5
    def test_should_RoundToTheNext5MinuteIntervalNumber_When_ANumberIsGiven(self):
        self.assertEqual(round_minutes_to_5(123), 125)
        self.assertEqual(round_minutes_to_5(88), 90)

    #Test for convert_iso_to_erpnext_datetime
    def test_should_ConvertISOToErpnextDatetime_When_ISOStringIsGiven(self):
        iso_str = "2025-01-01T10:30:00Z" # UTC
        erp_dt = convert_iso_to_erpnext_datetime(iso_str)

        #In Funktion wird + 1h gerechnet weil Zeitzone Zürich + 1h von UTC ist
        self.assertEqual(erp_dt, "2025-01-01 11:30:00")

    #Tests for build_html_link
    def test_should_ReturnCorrectHTMLLink_When_ALinkIsGiven(self):
        link = build_html_link("http://example.com", "Klicke hier")

        self.assertIn("<a href=", link)
        self.assertIn("http://example.com", link)
        self.assertIn("Klicke hier", link)
