"""
Original code and data by Kliemann
"""
from typing import List

import utm

from util import *


class Dortmund(ScraperBase):

    POOL = PoolInfo(
        id="hamburg",
        name="Hamburg",
        public_url="https://www.hamburg.de/parken/",
        source_url="https://geodienste.hamburg.de/HH_WFS_Verkehr_opendata?service=WFS&request=GetFeature&VERSION=1.1.0&typename=verkehr_parkhaeuser",
        timezone="UTC",
        attribution_contributor=None,
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        lots = []
        last_updated = self.to_utc_datetime(self.soup.find('wfs:featurecollection')["timestamp"])

        for member in self.soup.find('wfs:featurecollection').find_all('gml:featuremember'):
            count = None
            try:
                count = int(member.find('app:stellplaetze_gesamt').string)
            except AttributeError:
                pass

            free = None
            state = "nodata"
            situation = member.find('app:situation')
            if situation and situation.string != "keine Auslastungsdaten":
                free = int(member.find('app:frei').string)
                status = member.find('app:status').string
                if status == "frei" or status == "besetzt":
                    state = "open"
                else:
                    state = "closed"

            lot_id = member.find('app:id').string

            lots.append(
                LotData(
                    timestamp=self.request_timestamp,
                    lot_timestamp=last_updated,
                    # TODO: Note that original id is just 'lot_id' without the prefix
                    #   but that's not a good idea.
                    id=name_to_id("hamburg", lot_id),
                    capacity=count,
                    num_free=free,
                    status=state,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        self.request_timestamp = self.now()
        self.soup = self.request_soup(self.POOL.source_url)

        lots = []

        for member in self.soup.find('wfs:featurecollection').find_all('gml:featuremember'):
            name = member.find('app:name').string
            count = None
            try:
                count = int(member.find('app:stellplaetze_gesamt').string)
            except AttributeError:
                pass

            lot_type = member.find('app:art').string
            if lot_type == "Straßenrand":
                lot_type = "Parkplatz"
            lot_type = guess_lot_type(lot_type)

            lot_id = member.find('app:id').string
            address = ""
            try:
                address = member.find('app:einfahrt').string
            except AttributeError:
                try:
                    address = member.find('app:strasse').string
                    try:
                        address += " " + member.find('app:hausnr').string
                    except (AttributeError, TypeError):
                        pass
                except AttributeError:
                    pass
            address = address.lstrip(" ,")

            coord_member = member.find('gml:pos')
            if coord_member:
                coord_string = coord_member.string.split()
                latlon = utm.to_latlon(float(coord_string[0]), float(coord_string[1]), 32, 'U')
                coords = {
                    "lat": latlon[0],
                    "lng": latlon[1]
                }
            else:
                coords = None

            lots.append(
                LotInfo(
                    id=name_to_id("hamburg", lot_id),
                    name=name,
                    type=lot_type,
                    address=address or None,
                    capacity=count,
                    has_live_capacity=True,
                    latitude=coords["lat"] if coords else None,
                    longitude=coords["lng"] if coords else None,
                )
            )

        return lots

