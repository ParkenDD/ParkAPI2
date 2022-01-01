"""
Original code and data by Quint
"""
from typing import List

from util import *


class Heidelberg(ScraperBase):

    POOL = PoolInfo(
        id="heidelberg",
        name="Heidelberg",
        public_url="https://parken.heidelberg.de",
        source_url="https://parken.heidelberg.de/v1/parking-location?key=3wU8F-5QycD-ZbaW9-R6uvj-xm1MG-X07ne",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Heidelberg",
        attribution_license=None,
        attribution_url=None,
    )

    ALLOW_SSL_FAILURE = "expired"
    HEADERS = {
        "Accept": "application/json; charset=utf-8",
        "Referer": "https://parken.heidelberg.de/",
    }

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        dataJSON = self.request_json(self.POOL.source_url)

        lots = []

        last_updated = self.to_utc_datetime(dataJSON['data']['updated'])

        for parking_lot in dataJSON['data']['parkinglocations'] :
            # please keep the name in the geojson-file in the same form as delivered here (including spaces)
            parking_name = ('P'+str(parking_lot['uid'])+' '+parking_lot['name']).strip()

            try:
                parking_capacity = int(parking_lot['parkingupdate']['total'])
                parking_occupied = int(parking_lot['parkingupdate']['current'])
                parking_state = LotData.Status.open

                if parking_lot['parkingupdate']['status'] == 'closed':
                    parking_state = LotData.Status.closed
                # TODO: There is also a parking_lot['is_closed'] flag
                #   which does not necessarily match the status above
                #   but the `parken.heidelberg.de` website actually
                #   considers both status to display a lot as closed
            except:
                parking_state = LotData.Status.nodata
                parking_occupied = None
                parking_capacity = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=name_to_legacy_id("heidelberg", parking_name),
                    status=parking_state,
                    num_occupied=parking_occupied,
                    capacity=parking_capacity,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name.strip(): lot
            for lot in self.get_v1_lot_infos_from_geojson("Heidelberg")
        }

        dataJSON = self.request_json(self.POOL.source_url)

        lots = []

        for parking_lot in dataJSON['data']['parkinglocations'] :
            # please keep the name in the geojson-file in the same form as delivered here (including spaces)
            parking_name = ('P'+str(parking_lot['uid'])+' '+parking_lot['name']).strip()

            try:
                parking_capacity = int(parking_lot['parkingupdate']['total'])
            except:
                parking_capacity = None

            original_lot = vars(lot_map.get(parking_name) or dict())

            lots.append(
                LotInfo(
                    id=name_to_legacy_id("heidelberg", parking_name),
                    type=original_lot.get("type"),
                    name=parking_name,
                    capacity=parking_capacity,
                    public_url=parking_lot.get("website"),
                    has_live_capacity=True,
                    address=parking_lot["address"].replace(" ,", ",").strip(" ,").replace(", ", "\n"),
                    latitude=original_lot.get("latitude"),
                    longitude=original_lot.get("longitude"),
                )
            )

        return lots
