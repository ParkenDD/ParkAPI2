"""
Original code and data by Quint, Kliemann
"""
import json
from typing import List

import bs4

from util import *


class Koeln(ScraperBase):

    POOL = PoolInfo(
        id="koeln",
        name="Köln",
        public_url="https://offenedaten-koeln.de/dataset/parkhausbelegung",
        source_url="https://www.stadt-koeln.de/externe-dienste/open-data/parking-ts.php",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Köln",
        attribution_license="Datenlizenz Deutschland – Zero – Version 2.0",
        attribution_url="https://www.govdata.de/dl-de/zero-2-0",
    )

    @classmethod
    def normalize_lot_name(cls, name: str) -> str:
        if "- nur bei Veranstaltungen" in name:
            name = name.split("- nur bei Veranstaltungen", 1)[0].strip()
        return name

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        data = self.request_json(self.POOL.source_url)
        lots = []

        for feature in data["features"]:

            name = feature["attributes"]["parkhaus"]
            if not name:
                # Can not handle these as we
                #   would need the ID -> Name mapping
                continue

            name = self.normalize_lot_name(name)
            num_free = feature["attributes"]["kapazitaet"]
            # tendency = feature["attributes"]["tendenz"]

            if num_free < 0:
                num_free = None
                status = LotData.Status.nodata
            else:
                status = LotData.Status.open

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=self.to_utc_datetime(feature["attributes"]["timestamp"]),
                    id=name_to_id("koeln", feature["attributes"]["identifier"]),
                    status=status,
                    num_free=num_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        # beautify the legacy names a bit
        NAME_MAPPING = {
            "Theater/ Krebsgasse": "Theater-Parkhaus",
        }
        original_lots = self.get_v1_lot_infos_from_geojson("Koeln", include_original=True)
        for lot, feature in original_lots:
            feature["properties"]["aux"] = json.loads(feature["properties"]["aux"])

        lot_map = {
            feature["properties"]["aux"]["identifier"].upper(): lot
            for lot, feature in original_lots
        }

        data = self.request_json(self.POOL.source_url)
        lots = []

        for feature in data["features"]:

            lot = lot_map[feature["attributes"]["identifier"].upper()]
            lot.name = NAME_MAPPING.get(lot.name, lot.name).replace("trasse", "traße")
            lot.id = name_to_id("koeln", feature["attributes"]["identifier"])
            lots.append(lot)

        return lots
