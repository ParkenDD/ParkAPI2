"""
Original code and data by Quint
"""
from typing import List

from util import *


class Regensburg(ScraperBase):

    POOL = PoolInfo(
        id="regensburg",
        name="Regensburg",
        public_url="https://www.einkaufen-regensburg.de/service/parken-amp-anfahrt.html",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor=None,
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        parking_lots = soup.find_all("div", class_="accordeon parkmoeglichkeit")
        for one_lot in parking_lots:

            parking_belegung = one_lot.find("div", class_="belegung")
            # skip lots without live-data
            if not parking_belegung:
                continue

            parking_name = one_lot.find("h3").text

            parking_state = LotData.Status.open
            parking_free = None
            try:
                parking_free = int(parking_belegung.find("strong").text)
            except:
                parking_state = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("regensburg", parking_name),
                    status=parking_state,
                    num_free=parking_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lots = self.get_v1_lot_infos_from_geojson("Regensburg")
        for lot in lots:
            # this name has changed
            if lot.name == "Tiefgarage Castra Regina Center":
                lot.name = "Tiefgarage Hauptbahnhof/Castra Regina Center"
                lot.id = name_to_legacy_id("regensburg", lot.name)

        return lots
