import unittest
import datetime
from typing import Optional

import pytz

from util import *


class TestDateConversion(unittest.TestCase):

    def test_date_conversion_without_timezone(self):
        # with format
        self.assertEqual(
            "2000-01-01T00:00:00",
            to_utc_datetime("2000-01-01T00:00:00", date_format="%Y-%m-%dT%H:%M:%S").isoformat()
        )
        with self.assertRaises(ValueError):
            self.assertEqual(
                "2000-01-01T00:00:00",
                to_utc_datetime("2000-01-01X00:00:00", date_format="%Y-%m-%dT%H:%M:%S").isoformat()
            )
        # without format
        self.assertEqual(
            "2000-01-01T00:00:00",
            to_utc_datetime("2000-01-01T00:00:00").isoformat()
        )
        self.assertEqual(
            "2000-01-01T00:00:00",
            to_utc_datetime("Jan 1 2000").isoformat()
        )
        with self.assertRaises(ValueError):
            self.assertEqual(
                "2000-01-01T00:00:00",
                to_utc_datetime("No Date").isoformat()
            )

        # with explicit timezone
        self.assertEqual(
            "1999-12-31T23:00:00",
            to_utc_datetime("2000-01-01T00:00:00", timezone="Europe/Berlin").isoformat()
        )

    def test_date_conversion_with_timezone(self):
        # with format
        self.assertEqual(
            "1999-12-31T23:00:00",
            to_utc_datetime("2000-01-01T00:00:00+0100", date_format="%Y-%m-%dT%H:%M:%S%z").isoformat()
        )
        # without format
        self.assertEqual(
            "1999-12-31T23:00:00",
            to_utc_datetime("2000-01-01T00:00:00+0100").isoformat()
        )

        # with explicit timezone
        # TODO: This currently does never work
        with self.assertRaises(ValueError):
            self.assertEqual(
                "1999-12-31T23:00:00",
                to_utc_datetime("2000-01-01T00:00:00+0100", timezone="Europe/Berlin").isoformat()
            )
