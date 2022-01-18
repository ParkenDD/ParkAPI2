"""
Original code and data by Költzsch, Thalheim
"""
from typing import List

from util import *


class Ingolstadt(ScraperBase):

    POOL = PoolInfo(
        id="ingolstadt",
        name="Ingolstadt",
        public_url="https://www.ingolstadt.mobi/parkplatzauskunft.cfm",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Ingolstadt",
        attribution_license=None,
        attribution_url="https://www.ingolstadt.mobi/impressum.cfm",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        last_updated = self.to_utc_datetime(soup.p.string, "(%d.%m.%Y, %H.%M Uhr)")

        raw_lots = soup.find_all("tr")
        for raw_lot in raw_lots:
            elements = raw_lot.find_all("td")

            lot_name = elements[0].text

            state = LotData.Status.open
            if "class" in raw_lot.attrs and "strike" in raw_lot["class"]:
                state = LotData.Status.closed

            try:
                num_free = int(elements[1].text)
            except:
                num_free = None
                state = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("ingolstadt", lot_name),
                    status=state,
                    num_free=num_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        return self.get_v1_lot_infos_from_geojson("Ingolstadt")
