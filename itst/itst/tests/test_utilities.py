import unittest
from itst.itst.integrations.clockify.utilities import (
    parse_duration,
    parse_hhmm_to_minutes,
    minutes_to_hhmm,
    round_minutes_to_5,
    convert_iso_to_erpnext_datetime,
    build_html_link,
    get_week_start_iso
)

class TestUtilities(unittest.TestCase):
    def test_shouldReturnCorrectDurationAndHours_whenParsingDuration(self):
        hours, duration_str = parse_duration("PT1H30M")
        self.assertEqual(hours, 1.5)
        self.assertEqual(duration_str, "1:30")

    def test_shouldThrowError_whenParsingInvalidDurationString(self):
        with self.assertRaises(ValueError):
            parse_duration("XYZ")

    def test_shouldReturnMinutes_whenGivenHHmmFormat(self):
        total_minutes = parse_hhmm_to_minutes("2:05")
        self.assertEqual(total_minutes, 125)

    def test_shouldReturnHHmm_whenGivenTotalMinutes(self):
        hhmm = minutes_to_hhmm(125)
        self.assertEqual(hhmm, "2:05")
    
    def test_shouldRoundToNearest5Minutes_whenGivenAnyNumberOfMinutes(self):
        self.assertEqual(round_minutes_to_5(123), 125)
        self.assertEqual(round_minutes_to_5(88), 90)

    def test_shouldConvertISOToErpnextDatetime_whenGivenISOString(self):
        # UTC 10:30 => +1h => 11:30
        iso_str = "2025-01-01T10:30:00Z" # UTC
        erp_dt = convert_iso_to_erpnext_datetime(iso_str)
        self.assertEqual(erp_dt, "2025-01-01 11:30:00")

    def test_shouldReturnCorrectHtmlLink_whenGivenUrlAndText(self):
        link = build_html_link("http://example.com", "Klicke hier")
        self.assertIn("<a href=", link)
        self.assertIn("http://example.com", link)
        self.assertIn("Klicke hier", link)
    
    def test_shouldReturnWeekStartIso_whenCalled(self):
        iso_val = get_week_start_iso()
        self.assertIn("T00:00:00Z", iso_val)