"""
Original code and data by sssman
"""
import html
from typing import List, Tuple, Union, Optional

import feedparser

from util import *


class Basel(ScraperBase):

    POOL = PoolInfo(
        id="basel",
        name="Basel",
        public_url="https://www.parkleitsystem-basel.ch/",
        source_url="https://www.parkleitsystem-basel.ch/alte_site/rss_feed.php",
        timezone="Europe/Berlin",
        attribution_contributor="Immobilien Basel-Stadt",
        attribution_license="Creative-Commons-Null-Lizenz (CC-0)",
        attribution_url="https://www.parkleitsystem-basel.ch/alte_site/impressum.php",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        response = self.request(self.POOL.source_url)
        feed = feedparser.parse(response.text)

        lots = []

        for entry in feed.get("entries", []):
            status, num_free = self.parse_summary(entry["summary"])
            title = html.unescape(entry["title"].strip())

            lots.append(
                LotData(
                    timestamp=now,
                    lot_timestamp=self.to_utc_datetime(entry["updated"][5:]),
                    id=name_to_legacy_id("basel", title),
                    status=status,
                    num_free=num_free,
                )
            )

        return lots

    @staticmethod
    def parse_summary(summary) -> Tuple[str, Optional[int]]:
        """
        Parse a string from the format 'Anzahl freie Parkpl&auml;tze: 179' into both its params
        """
        status = LotData.Status.open
        num_free = None

        summary = summary.split(":")

        summary[0] = summary[0].strip()
        if "?" in summary[0]:
            status = LotData.Status.nodata

        try:
            num_free = int(summary[1])
        except ValueError:
            status = LotData.Status.nodata

        return status, num_free
