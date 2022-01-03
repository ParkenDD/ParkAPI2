"""
Original code and data by Quint
"""
from typing import List

from util import *


class Rosenheim(ScraperBase):

    POOL = PoolInfo(
        id="rosenheim",
        name="Rosenheim",
        public_url="https://www.rosenheim.de/stadt-buerger/verkehr/parken.html",
        source_url="https://www.rosenheim.de/index.php?eID=jwParkingGetParkings",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Rosenheim",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        dataJSON = self.request_json(self.POOL.source_url)

        lots = []

        # over all parking-lots
        for parking_lot in dataJSON :
            parking_name = parking_lot['title']
            if parking_name != 'Reserve':
                parking_status = (
                    LotData.Status.open if parking_lot['isOpened']
                    else LotData.Status.closed
                )

                lots.append(
                    LotData(
                        timestamp=timestamp,
                        id=name_to_legacy_id("rosenheim", parking_name),
                        status=parking_status,
                        num_free=int_or_none(parking_lot['free']),
                        capacity=int_or_none(parking_lot["parkings"]),
                    )
                )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        LEGACY_TO_NEW_NAME = {
            "P8 Beilhack-Citydome": "P8 Beilhack-Kinopolis",
            "P11 Beilhack-Gießereistr.": "P11 Beilhack-Gießereistraße",
        }
        lots = self.get_v1_lot_infos_from_geojson("Rosenheim")
        for lot in lots:
            lot.has_live_capacity = True
            if lot.name in LEGACY_TO_NEW_NAME:
                lot.name = LEGACY_TO_NEW_NAME[lot.name]
                lot.id = name_to_legacy_id("rosenheim", lot.name)

        return lots
