"""
Original code and data by Quint.
"""
import re
import urllib.parse
from typing import List

from util import *


class Dortmund(ScraperBase):

    POOL = PoolInfo(
        id="dortmund",
        name="Dortmund",
        public_url="https://www.dortmund.de/",
        source_url="https://geoweb1.digistadtdo.de/OWSServiceProxy/client/parken.jsp",
        timezone="Europe/Berlin",
        attribution_contributor=None,
        attribution_license=None,
        attribution_url=None,
    )

    RE_PARKING_SPACES = re.compile(r".*(\d+) Plätze von (\d+) frei.*")

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []
        last_updated = self.to_utc_datetime(soup.find('h2').text, "Stand: %d.%m.%Y %H:%M Uhr")

        for parking_lot in soup.find_all('dl'):
            parking_name = parking_lot.find('dt').text

            match = self.RE_PARKING_SPACES.match(parking_lot.find('dd').text)
            if match:
                parking_state = LotData.Status.open
                parking_numbers = [int(n) for n in match.groups()]
            else:
                parking_state = LotData.Status.nodata
                parking_numbers = [None, None]

            lots.append(
                LotData(
                    timestamp=now,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("dortmund", parking_name),
                    num_free=parking_numbers[0],
                    capacity=parking_numbers[1],
                    status=parking_state,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.source_url)

        name_to_url_map = dict()
        for parking_lot in soup.find_all('dl'):
            a = parking_lot.find("dt").find("a")
            name_to_url_map[a.text] = urllib.parse.urljoin(self.POOL.source_url, a["href"])

        lots = self.get_v1_lot_infos_from_geojson(
            name="Dortmund",
            defaults={
                "has_live_capacity": True,
            }
        )

        for lot in lots:
            lot.public_url = name_to_url_map[lot.name]

        return lots
