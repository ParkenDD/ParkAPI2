"""
Original code and data by Költzsch, Thalheim
"""
import urllib.parse
from typing import List

from util import *


class Muenster(ScraperBase):

    POOL = PoolInfo(
        id="muenster",
        name="Münster",
        public_url="https://www.stadt-muenster.de/tiefbauamt/parkleitsystem",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Amt für Mobilität und Tiefbau Münster",
        attribution_license=None,
        attribution_url="https://www.stadt-muenster.de/tiefbauamt/impressum.html",
    )

    STATE_MAP = {
        "frei": LotData.Status.open,
        "geschlossen": LotData.Status.closed,
        "besetzt": LotData.Status.open,
    }

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        lot_table_trs = soup.select("div#parkingList table")[0].find_all("tr")
        date_field = soup.find(id="lastRefresh").text.strip()
        last_updated = self.to_utc_datetime(date_field, "%d.%m.%Y %H:%M Uhr")

        for tr in lot_table_trs[1:-1]:
            tds = tr.find_all("td")
            type_and_name = self.process_name(tds[0].text.strip())
            parking_name = tds[0].text.strip()

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("muenster", parking_name),
                    status=self.STATE_MAP.get(tds[2].text, LotData.Status.unknown),
                    num_free=int_or_none(tds[1].text),
                )
            )

        return lots

    @classmethod
    def process_name(cls, name):
        split_name = name.split()
        lot_type = split_name[0]
        lot_name = (split_name[0] if len(split_name) == 1 else " ".join(split_name[1:])).strip()

        type_mapping = {
            "PP": LotInfo.Types.lot,
            "PH": LotInfo.Types.garage,
            "Busparkplatz": LotInfo.Types.bus,
        }
        lot_type = type_mapping.get(lot_type, LotInfo.Types.unknown)

        return lot_type, lot_name

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Muenster")
        }

        soup = self.request_soup(self.POOL.public_url)

        lots = []

        lot_table_trs = soup.select("div#parkingList table")[0].find_all("tr")

        for tr in lot_table_trs[1:-1]:
            tds = tr.find_all("td")
            type_and_name = self.process_name(tds[0].text.strip())
            parking_name = tds[0].text.strip()

            kwargs = vars(lot_map[parking_name])
            kwargs.update(dict(
                public_url=urllib.parse.urljoin(self.POOL.public_url, tr.find("a")["href"]),
                type=type_and_name[0],
            ))

            lots.append(LotInfo(**kwargs))

        return lots
