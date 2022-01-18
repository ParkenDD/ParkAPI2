"""
Original code and data by Wieland
"""
from typing import List

from util import *


class Dortmund(ScraperBase):

    POOL = PoolInfo(
        id="freiburg",
        name="Freiburg",
        public_url="https://www.freiburg.de/pb/,Lde/231355.html",
        source_url="https://geoportal.freiburg.de/wfs/gdm_pls/gdm_plslive?request=getfeature&service=wfs&version=1.1.0&typename=pls&outputformat=geojson&srsname=epsg:4326",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Freiburg",
        attribution_license="dl-de/by-2-0",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        geojson = self.request_json(self.POOL.source_url)

        lots = []

        for feature in geojson["features"]:
            lot_name = feature['properties']['park_name']
            lot_free = int(feature['properties']['obs_free'])
            # lot_total = int(feature['properties']['obs_max'])

            obs_ts = self.to_utc_datetime(feature['properties']['obs_ts'])

            # please be careful about the state only being allowed to contain either open, closed or nodata
            # should the page list other states, please map these into the three listed possibilities
            state = LotData.Status.nodata

            if feature['properties']['obs_state'] == "1":
                state = LotData.Status.open
            elif feature['properties']['obs_state'] == "0":
                state = LotData.Status.closed

            lots.append(
                LotData(
                    timestamp=now,
                    lot_timestamp=obs_ts,
                    id=name_to_legacy_id("freiburg", lot_name),
                    status=state,
                    num_free=lot_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson(
                name="Freiburg",
                defaults={
                    "has_live_capacity": True,
                }
            )
        }

        geojson = self.request_json(self.POOL.source_url)

        lots = []

        for feature in geojson["features"]:
            lot_name = feature['properties']['park_name']
            lot_total = int(feature['properties']['obs_max'])
            public_url = feature["properties"]["park_url"].replace("http://", "https://")

            kwargs = {
                "id": name_to_legacy_id("freiburg", lot_name),
                "name": lot_name,
                "type": LotInfo.Types.unknown,
            }
            if lot_map.get(lot_name):
                kwargs = vars(lot_map[lot_name])
            kwargs.update({
                "capacity": lot_total,
                "public_url": public_url,
            })
            lots.append(LotInfo(**kwargs))

        return lots
