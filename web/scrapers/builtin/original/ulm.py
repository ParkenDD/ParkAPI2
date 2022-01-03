"""
Original code and data by Quint
"""
from typing import List

from util import *


class Ulm(ScraperBase):

    POOL = PoolInfo(
        id="ulm",
        name="Ulm",
        public_url="https://www.parken-in-ulm.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Ulmer Parkbetriebs-GmbH",
        attribution_license=None,
        attribution_url="https://www.parken-in-ulm.de/impressum.php",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        table = soup.find('table', id='haupttabelle')
        table2 = table.find('table', width='790')
        rows = table2.find_all('tr')
        for row in rows[3:12]:
            parking_data = row.find_all('td')
            parking_name = parking_data[0].text

            try:
                parking_state = LotData.Status.open
                parking_free = int(parking_data[2].text)
            except:
                parking_free = None
                parking_state = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("ulm", parking_name),
                    status=parking_state,
                    num_free=parking_free,
                    capacity=int_or_none(parking_data[1].text),
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        return self.get_v1_lot_infos_from_geojson("Ulm")
