"""
Original code and data by Koeltzsch, Kliemann
"""
import warnings
from typing import List, Tuple, Optional

import feedparser

from util import *


class Zuerich(ScraperBase):

    POOL = PoolInfo(
        id="zuerich",
        name="Zuerich",
        public_url="https://data.stadt-zuerich.ch/dataset/parkleitsystem",
        source_url="https://www.pls-zh.ch/plsFeed/rss",
        timezone="GMT",
        attribution_contributor="PLS Parkleitsystem Zürich AG",
        attribution_license="Creative-Commons-Null-Lizenz (CC-0)",
        attribution_url="https://www.plszh.ch/impressum.jsp",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        response = self.request(self.POOL.source_url)
        feed = feedparser.parse(response.text)

        lots = []
        for entry in feed["entries"]:
            status, num_free = self.parse_summary(entry["summary"])
            name, address, type = self.parse_title(entry["title"])

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=to_utc_datetime(entry["date"]),
                    id=name_to_legacy_id("zuerich", name),
                    status=status,
                    num_free=num_free,
                )
            )

        return lots

    @classmethod
    def parse_summary(cls, summary) -> Tuple[str, Optional[int]]:
        """Parse a string from the format 'open /   41' into both its params"""
        summary = summary.split("/")

        status = summary[0].strip()
        if status not in vars(LotData.Status):
            status = LotData.Status.unknown

        try:
            num_free = int(summary[1])
        except ValueError:
            num_free = None
        return status, num_free

    @classmethod
    def parse_title(cls, title) -> Tuple[str, str, str]:
        """
        Parse a string from the format 'Parkgarage am Central / Seilergraben'
        into name, address and the lot_type
        """
        name, address = title.split(" / ")
        lot_type = guess_lot_type(name) or LotInfo.Types.unknown

        return name, address, lot_type

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Zuerich")
        }

        response = self.request(self.POOL.source_url)
        feed = feedparser.parse(response.text)
        lots = []

        for entry in feed["entries"]:
            name, address, type = self.parse_title(entry["title"])

            if name in lot_map:
                kwargs = vars(lot_map[name])
            else:
                warnings.warn(f"Lot '{name}' not in original geojson")
                kwargs = {
                    "id": name_to_legacy_id("zuerich", name),
                    "name": name,
                    "type": type,
                }
            kwargs.update({
                "address": address,
                "public_url": entry["links"][0]["href"],
            })

            lots.append(LotInfo(**kwargs))

        return lots
