"""
Original code and data by Ciosici
"""
from typing import List

from util import *


class Aarhus(ScraperBase):

    POOL = PoolInfo(
        id="aarhus",
        name="Aarhus",
        public_url="https://www.odaa.dk/dataset/parkeringshuse-i-aarhus",
        source_url="https://www.odaa.dk/api/action/datastore_search?resource_id=2a82a145-0195-4081-a13c-b0e587e9b89c",
        timezone="Europe/Berlin",
        attribution_contributor="Manuel R. Ciosici",
        attribution_license="Aarhus License – https://www.odaa.dk/base/image/Vilkår%20for%20brug%20af%20danske%20offentlige%20data%20-%20Aarhus%20Kommune.%20docx.pdf",
        attribution_url="https://www.odaa.dk/dataset/parkeringshuse-i-aarhus",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        data = self.request_json(self.POOL.source_url)

        lots = []

        # The page at https://www.odaa.dk/dataset/parkeringshuse-i-aarhus describes how the counts are made
        map_json_names = {
            "NORREPORT": "Nørreport",
            # "SKOLEBAKKEN": None,
            "SCANDCENTER": "Scandinavian Center",
            "BRUUNS": "Bruuns Galleri",
            "MAGASIN": "Magasin",
            "KALKVAERKSVEJ": "Kalkværksvej",
            "SALLING": "Salling",
            "Navitas": "Navitas",
            "NewBusgadehuset": "Busgadehuset",
            # cumulatives:
            "Urban Level 1": "Dokk1",
            "Urban Level 2+3": "Dokk1"
        }

        for record in data["result"]["records"]:
            lot_code = record["garageCode"]
            capacity = int(record["totalSpaces"])
            num_occupied = int(record["vehicleCount"])

            if lot_code not in map_json_names.keys():
                continue

            lot_name = map_json_names[lot_code]
            lot_id = name_to_legacy_id("aarhus", lot_name)

            existing_lot = None
            for lot in lots:
                if lot.id == lot_id:
                    existing_lot = lot
                    break

            if existing_lot:
                existing_lot.capacity += capacity
                existing_lot.num_occupied += num_occupied
                existing_lot.num_free = existing_lot.capacity - existing_lot.num_occupied
            else:
                lots.append(
                    LotData(
                        timestamp=now,
                        lot_timestamp=self.to_utc_datetime(record["date"]),
                        id=lot_id,
                        status=LotData.Status.open,
                        num_occupied=num_occupied,
                        capacity=capacity,
                    )
                )

        return lots
